from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.calendar_web import _can_write, _user
from familienportal.database import get_db
from familienportal.permissions import has_permission
from familienportal.platform_runtime import enabled_modules

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _period(mode: str, anchor: date) -> tuple[datetime, datetime, str, date, date]:
    if mode == "day":
        start_date = end_date = anchor
        title = anchor.strftime("%d.%m.%Y")
    elif mode == "week":
        start_date = anchor - timedelta(days=anchor.weekday())
        end_date = start_date + timedelta(days=6)
        title = f"{start_date.strftime('%d.%m.')} – {end_date.strftime('%d.%m.%Y')}"
    else:
        mode = "month"
        start_date = anchor.replace(day=1)
        end_date = anchor.replace(day=monthrange(anchor.year, anchor.month)[1])
        title = anchor.strftime("%m/%Y")
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start, end, title, start_date, end_date


def _shift(mode: str, anchor: date, amount: int) -> date:
    if mode == "day":
        return anchor + timedelta(days=amount)
    if mode == "week":
        return anchor + timedelta(days=7 * amount)
    month = anchor.month - 1 + amount
    year = anchor.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


@router.get("/calendar/view", response_class=HTMLResponse)
def calendar_view(
    request: Request,
    mode: str = Query("month", pattern="^(month|week|day)$"),
    at: str | None = None,
    calendar_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    user = _user(request, db)
    if not has_permission(user, "calendar.read"):
        raise HTTPException(status_code=403, detail="Keine Kalenderberechtigung")
    try:
        anchor = date.fromisoformat(at) if at else datetime.now(timezone.utc).date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges Datum") from exc
    start, end, title, start_date, end_date = _period(mode, anchor)
    calendars = db.scalars(select(Calendar).where(Calendar.family_id == user.family_id, Calendar.is_visible.is_(True)).order_by(Calendar.name)).all()
    query = select(CalendarEvent).where(
        CalendarEvent.family_id == user.family_id,
        CalendarEvent.deleted_at.is_(None),
        CalendarEvent.starts_at < end,
        CalendarEvent.ends_at >= start,
    )
    if calendar_id:
        query = query.where(CalendarEvent.calendar_id == calendar_id)
    events = db.scalars(query.order_by(CalendarEvent.starts_at)).all()
    cal_by_id = {item.id: item for item in calendars}
    days = []
    cursor = start_date
    while cursor <= end_date:
        day_events = [event for event in events if event.starts_at.date() <= cursor <= event.ends_at.date()]
        days.append({"date": cursor, "events": day_events})
        cursor += timedelta(days=1)
    navigation_modules = [item for item in enabled_modules(db, user.family_id, user) if item.get("menu")]
    return templates.TemplateResponse(request=request, name="calendar_view.html", context={
        "user": user,
        "is_admin": user.is_superadmin or any(role.name == "Administrator" for role in user.roles),
        "navigation_modules": navigation_modules,
        "mode": mode,
        "anchor": anchor,
        "title": title,
        "days": days,
        "events": events,
        "calendars": calendars,
        "cal_by_id": cal_by_id,
        "selected_calendar_id": calendar_id,
        "prev_at": _shift(mode, anchor, -1),
        "next_at": _shift(mode, anchor, 1),
        "can_write": _can_write(user),
    })


@router.post("/calendar/calendars/{calendar_id}/appearance")
def calendar_appearance(calendar_id: UUID, request: Request, color: str = Form("#0d6efd"), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    calendar = db.get(Calendar, calendar_id)
    if not calendar or calendar.family_id != user.family_id:
        raise HTTPException(status_code=404, detail="Kalender nicht gefunden")
    if len(color) != 7 or not color.startswith("#"):
        raise HTTPException(status_code=400, detail="Ungültige Farbe")
    calendar.color = color
    db.commit()
    return RedirectResponse("/calendar/view", status_code=303)


@router.get("/calendar/events/{event_id}/edit", response_class=HTMLResponse)
def edit_event_page(event_id: UUID, request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    event = db.get(CalendarEvent, event_id)
    if not event or event.family_id != user.family_id or event.deleted_at:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    calendars = db.scalars(select(Calendar).where(Calendar.family_id == user.family_id).order_by(Calendar.name)).all()
    return templates.TemplateResponse(request=request, name="calendar_event_edit.html", context={"user": user, "is_admin": user.is_superadmin, "event": event, "calendars": calendars})


@router.post("/calendar/events/{event_id}/edit")
def edit_event(
    event_id: UUID,
    request: Request,
    calendar_id: UUID = Form(...),
    title: str = Form(...),
    starts_at: str = Form(...),
    ends_at: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    event = db.get(CalendarEvent, event_id)
    calendar = db.get(Calendar, calendar_id)
    if not event or event.family_id != user.family_id or not calendar or calendar.family_id != user.family_id:
        raise HTTPException(status_code=404, detail="Termin oder Kalender nicht gefunden")
    try:
        start = datetime.fromisoformat(starts_at)
        end = datetime.fromisoformat(ends_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges Datum") from exc
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end < start:
        raise HTTPException(status_code=400, detail="Ende liegt vor Beginn")
    event.calendar_id = calendar.id
    event.title = title.strip()
    event.starts_at = start
    event.ends_at = end
    event.description = description.strip() or None
    event.location = location.strip() or None
    event.updated_at = datetime.now(timezone.utc)
    audit(db, "calendar.event.updated", actor=user, target_type="calendar_event", target_id=str(event.id))
    db.commit()
    return RedirectResponse("/calendar/view", status_code=303)


@router.post("/calendar/events/{event_id}/move")
def move_event(event_id: UUID, request: Request, new_start: str = Form(...), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    event = db.get(CalendarEvent, event_id)
    if not event or event.family_id != user.family_id or event.deleted_at:
        raise HTTPException(status_code=404, detail="Termin nicht gefunden")
    try:
        target = datetime.fromisoformat(new_start)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültiger Zeitpunkt") from exc
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    duration = event.ends_at - event.starts_at
    event.starts_at = target
    event.ends_at = target + duration
    event.updated_at = datetime.now(timezone.utc)
    audit(db, "calendar.event.moved", actor=user, target_type="calendar_event", target_id=str(event.id))
    db.commit()
    return RedirectResponse("/calendar/view", status_code=303)
