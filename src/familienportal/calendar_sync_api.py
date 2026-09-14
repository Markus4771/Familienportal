from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.caldav import CalDAVClient
from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.calendar_sync import parse_event_ics, sync_binding
from familienportal.calendar_sync_models import CalendarEventSyncState, CalendarSyncBinding
from familienportal.database import get_db
from familienportal.nextcloud_web import _client as nextcloud_client
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin

router = APIRouter(prefix="/api/v1/calendar-sync", tags=["calendar-sync"])


def _caldav(db: Session, family_id) -> CalDAVClient:
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == family_id, ConnectorState.connector_key == "nextcloud"))
    if not state:
        raise HTTPException(status_code=409, detail="Nextcloud ist nicht konfiguriert")
    nc = nextcloud_client(state)
    return CalDAVClient(nc.base_url, nc.username, nc.password)


def _conflict(db: Session, family_id, event_id: UUID) -> tuple[CalendarEventSyncState, CalendarEvent]:
    state = db.scalar(
        select(CalendarEventSyncState)
        .join(CalendarSyncBinding)
        .where(
            CalendarSyncBinding.family_id == family_id,
            CalendarEventSyncState.event_id == event_id,
            CalendarEventSyncState.conflict.is_(True),
        )
    )
    event = db.get(CalendarEvent, event_id)
    if not state or not event or event.family_id != family_id:
        raise HTTPException(status_code=404, detail="Kalenderkonflikt nicht gefunden")
    return state, event


@router.get("/bindings")
def bindings(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    items = db.scalars(select(CalendarSyncBinding).where(CalendarSyncBinding.family_id == admin.family_id)).all()
    return [{"id": item.id, "calendar_id": item.calendar_id, "remote_href": item.remote_href, "remote_name": item.remote_name, "enabled": item.enabled, "last_status": item.last_status, "last_message": item.last_message, "last_sync_at": item.last_sync_at, "sync_token": item.sync_token} for item in items]


@router.post("/bindings")
def save_binding(request: Request, calendar_id: UUID = Form(...), remote_href: str = Form(...), remote_name: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    calendar = db.get(Calendar, calendar_id)
    if not calendar or calendar.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Kalender nicht gefunden")
    item = db.scalar(select(CalendarSyncBinding).where(CalendarSyncBinding.family_id == admin.family_id, CalendarSyncBinding.calendar_id == calendar_id))
    if not item:
        item = CalendarSyncBinding(family_id=admin.family_id, calendar_id=calendar_id, remote_href=remote_href.strip())
        db.add(item)
    item.remote_href = remote_href.strip()
    item.remote_name = remote_name.strip() or None
    item.enabled = True
    item.last_status = "configured"
    item.last_message = None
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.last_status}


@router.get("/conflicts")
def conflicts(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    items = db.scalars(select(CalendarEventSyncState).join(CalendarSyncBinding).where(CalendarSyncBinding.family_id == admin.family_id, CalendarEventSyncState.conflict.is_(True))).all()
    result = []
    for item in items:
        event = db.get(CalendarEvent, item.event_id)
        result.append({"event_id": item.event_id, "binding_id": item.binding_id, "remote_href": item.remote_href, "message": item.conflict_message, "title": event.title if event else "Unbekannt"})
    return result


@router.post("/conflicts/{event_id}/local")
def resolve_local(event_id: UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state, event = _conflict(db, admin.family_id, event_id)
    client = _caldav(db, admin.family_id)
    remote = client.get_object(state.remote_href)
    state.remote_etag = remote.etag
    state.conflict = False
    state.conflict_message = None
    state.last_local_updated_at = None
    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    binding = db.get(CalendarSyncBinding, state.binding_id)
    if binding:
        sync_binding(db, client, binding)
    return {"status": "resolved", "winner": "local"}


@router.post("/conflicts/{event_id}/remote")
def resolve_remote(event_id: UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state, event = _conflict(db, admin.family_id, event_id)
    remote = _caldav(db, admin.family_id).get_object(state.remote_href)
    try:
        parsed = parse_event_ics(remote.data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Remote-Termin kann nicht gelesen werden") from exc
    event.title = str(parsed["title"])
    event.description = parsed["description"]
    event.location = parsed["location"]
    event.starts_at = parsed["starts_at"]
    event.ends_at = parsed["ends_at"]
    event.recurrence_rule = parsed["recurrence_rule"]
    event.external_uid = str(parsed["uid"])
    event.source = "nextcloud"
    event.updated_at = datetime.now(timezone.utc)
    event.deleted_at = None
    state.remote_etag = remote.etag
    state.last_local_updated_at = event.updated_at
    state.conflict = False
    state.conflict_message = None
    db.commit()
    return {"status": "resolved", "winner": "remote"}


@router.post("/{binding_id}/run")
def run(binding_id: UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    binding = db.get(CalendarSyncBinding, binding_id)
    if not binding or binding.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Synchronisationszuordnung nicht gefunden")
    if not binding.enabled:
        raise HTTPException(status_code=409, detail="Synchronisation ist deaktiviert")
    return sync_binding(db, _caldav(db, admin.family_id), binding)
