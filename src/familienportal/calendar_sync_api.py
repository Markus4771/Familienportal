from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.caldav import CalDAVClient
from familienportal.calendar_sync import sync_binding
from familienportal.calendar_sync_models import CalendarSyncBinding
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


@router.get("/bindings")
def bindings(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    items = db.scalars(select(CalendarSyncBinding).where(CalendarSyncBinding.family_id == admin.family_id)).all()
    return [{"id": item.id, "calendar_id": item.calendar_id, "remote_href": item.remote_href, "remote_name": item.remote_name, "enabled": item.enabled, "last_status": item.last_status, "last_message": item.last_message, "last_sync_at": item.last_sync_at} for item in items]


@router.post("/{binding_id}/run")
def run(binding_id: UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    binding = db.get(CalendarSyncBinding, binding_id)
    if not binding or binding.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Synchronisationszuordnung nicht gefunden")
    return sync_binding(db, _caldav(db, admin.family_id), binding)
