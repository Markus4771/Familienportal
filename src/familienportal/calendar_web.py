from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.calendar_ics import calendar_to_ics
from familienportal.calendar_models import Birthday, Calendar, CalendarEvent
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.permissions import has_permission
from familienportal.platform_runtime import enabled_modules

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _user(request: Request, db: Session) -> User:
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    try:
        user = db.get(User, UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung") from exc
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    return user


def _can_write(user: User) -> bool:
    return has_permission(user, "calendar.write") or has_permission(user, "calendar.*")


def _bootstrap_calendars(db: Session, user: User) -> None:
    by_slug = {item.slug: item for item in db.scalars(select(Calendar).where(Calendar.family_id == user.family_id)).all()}
    defaults = [
        ("familie", "Familienkalender", "family"),
        ("geburtstage", "Geburtstage", "birthday"),
        ("veranstaltungen", "Veranstaltungen", "event"),
    ]
    changed = False
    for slug, name, kind in defaults:
        if slug not in by_slug:
            db.add(Calendar(family_id=user.family_id, name=name, slug=slug, kind=kind))
            changed = True
    personal_slug = f"user-{str(user.id)[:8]}"
    if personal_slug not in by_slug:
        db.add(Calendar(family_id=user.family_id, owner_user_id=user.id, name=f"{user.display_name} persönlich", slug=personal_slug, kind="personal"))
        changed = True
    if changed:
        db.commit()


@router.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    if not has_permission(user, "calendar.read"):
        raise HTTPException(status_code=403, detail="Keine Kalenderberechtigung")
    _bootstrap_calendars(db, user)
    calendars = db.scalars(select(Calendar).where(Calendar.family_id == user.family_id, Calendar.is_visible.is_(True)).order_by(Calendar.name)).all()
    events = db.scalars(select(CalendarEvent).where(CalendarEvent.family_id == user.family_id).order_by(CalendarEvent.starts_at).limit(250)).all()
    birthdays = db.scalars(select(Birthday).where(Birthday.family_id == user.family_id).order_by(Birthday.birth_date)).all()
    navigation_modules = [item for item in enabled_modules(db, user.family_id, user) if item.get("menu")]
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    return templates.TemplateResponse(request=request, name="calendar.html", context={
        "user": user,
        "is_admin": is_admin,
        "navigation_modules": navigation_modules,
        "calendars": calendars,
        "events": events,
        "birthdays": birthdays,
        "can_write": _can_write(user),
    })


@router.post("/calendar/calendars")
def create_calendar(request: Request, name: str = Form(...), slug: str = Form(...), kind: str = Form("family"), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    slug_value = slug.strip().lower().replace(" ", "-")
    if not slug_value:
        raise HTTPException(status_code=400, detail="Kalenderschlüssel fehlt")
    db.add(Calendar(family_id=user.family_id, owner_user_id=user.id if kind == "personal" else None, name=name.strip(), slug=slug_value, kind=kind))
    audit(db, "calendar.created", actor=user, target_type="calendar", target_id=slug_value)
    db.commit()
    return RedirectResponse("/calendar", status_code=303)


@router.post("/calendar/events")
def create_event(
    request: Request,
    calendar_id: UUID = Form(...),
    title: str = Form(...),
    starts_at: str = Form(...),
    ends_at: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    category: str = Form("general"),
    recurrence_rule: str = Form(""),
    reminder_minutes: str = Form(""),
    all_day: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    calendar = db.get(Calendar, calendar_id)
    if not calendar or calendar.family_id != user.family_id:
        raise HTTPException(status_code=404, detail="Kalender nicht gefunden")
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
        raise HTTPException(status_code=400, detail="Ende liegt vor dem Beginn")
    reminder = int(reminder_minutes) if reminder_minutes.strip().isdigit() else None
    item = CalendarEvent(
        family_id=user.family_id,
        calendar_id=calendar.id,
        created_by_user_id=user.id,
        title=title.strip(),
        description=description.strip() or None,
        location=location.strip() or None,
        starts_at=start,
        ends_at=end,
        all_day=all_day,
        category=category.strip() or "general",
        recurrence_rule=recurrence_rule.strip() or None,
        reminder_minutes=reminder,
    )
    db.add(item)
    db.flush()
    audit(db, "calendar.event.created", actor=user, target_type="calendar_event", target_id=str(item.id))
    db.commit()
    return RedirectResponse("/calendar", status_code=303)


@router.post("/calendar/birthdays")
def create_birthday(request: Request, name: str = Form(...), birth_date: str = Form(...), kind: str = Form("birthday"), note: str = Form(""), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not _can_write(user):
        raise HTTPException(status_code=403, detail="Keine Schreibberechtigung")
    try:
        parsed = datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges Datum") from exc
    db.add(Birthday(family_id=user.family_id, name=name.strip(), birth_date=parsed, kind=kind, note=note.strip() or None))
    audit(db, "calendar.birthday.created", actor=user, target_type="birthday", target_id=name.strip())
    db.commit()
    return RedirectResponse("/calendar", status_code=303)


@router.get("/calendar/{calendar_id}.ics", response_class=PlainTextResponse)
def export_calendar(calendar_id: UUID, request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    if not has_permission(user, "calendar.read"):
        raise HTTPException(status_code=403, detail="Keine Kalenderberechtigung")
    calendar = db.get(Calendar, calendar_id)
    if not calendar or calendar.family_id != user.family_id:
        raise HTTPException(status_code=404, detail="Kalender nicht gefunden")
    events = db.scalars(select(CalendarEvent).where(CalendarEvent.calendar_id == calendar.id).order_by(CalendarEvent.starts_at)).all()
    return PlainTextResponse(calendar_to_ics(calendar.name, list(events)), media_type="text/calendar; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{calendar.slug}.ics"'})
