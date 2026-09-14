from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.calendar_ics import parse_ics_events
from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.database import get_db
from familienportal.models import User
from familienportal.permissions import has_permission
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/calendar/import", response_class=HTMLResponse)
def import_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    calendars = db.scalars(select(Calendar).where(Calendar.family_id == admin.family_id).order_by(Calendar.name)).all()
    return templates.TemplateResponse(request=request, name="calendar_import.html", context={"user": admin, "is_admin": True, "calendars": calendars})


@router.post("/calendar/import")
def import_ics(request: Request, calendar_id: UUID = Form(...), ics_text: str = Form(...), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    calendar = db.get(Calendar, calendar_id)
    if not calendar or calendar.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Kalender nicht gefunden")
    try:
        imported = parse_ics_events(ics_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    count = 0
    for item in imported:
        uid = str(item.get("external_uid") or "") or None
        if uid and db.scalar(select(CalendarEvent).where(CalendarEvent.family_id == admin.family_id, CalendarEvent.external_uid == uid)):
            continue
        db.add(CalendarEvent(
            family_id=admin.family_id,
            calendar_id=calendar.id,
            created_by_user_id=admin.id,
            title=str(item["title"]),
            description=str(item.get("description") or "") or None,
            location=str(item.get("location") or "") or None,
            starts_at=item["starts_at"],
            ends_at=item["ends_at"],
            recurrence_rule=str(item.get("recurrence_rule") or "") or None,
            external_uid=uid,
            source="ics",
        ))
        count += 1
    audit(db, "calendar.ics.imported", actor=admin, target_type="calendar", target_id=str(calendar.id), details=f"count={count}")
    db.commit()
    return RedirectResponse(f"/calendar/import?imported={count}", status_code=303)
