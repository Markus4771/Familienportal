from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.gramps_calendar_dates import desired_events

CALENDAR_SLUG = "family-ancestry"
SOURCE = "gramps"


def ensure_calendar(db: Session, family_id: UUID) -> Calendar:
    calendar = db.scalar(select(Calendar).where(Calendar.family_id == family_id, Calendar.slug == CALENDAR_SLUG))
    if calendar:
        return calendar
    calendar = Calendar(
        family_id=family_id,
        name="Familie & Ahnen",
        slug=CALENDAR_SLUG,
        kind="genealogy",
        description="Automatisch aus Gramps Web synchronisierte Geburtstage und Gedenktage.",
        is_visible=True,
    )
    db.add(calendar)
    db.flush()
    return calendar


def sync_gramps_calendar(db: Session, family_id: UUID, people: list[dict], *, start_year: int | None = None, years: int = 3) -> dict[str, int]:
    calendar = ensure_calendar(db, family_id)
    year = start_year or datetime.now(timezone.utc).year
    desired = desired_events(people, year, years)
    existing = db.scalars(select(CalendarEvent).where(CalendarEvent.family_id == family_id, CalendarEvent.calendar_id == calendar.id, CalendarEvent.source == SOURCE)).all()
    by_uid = {item.external_uid: item for item in existing if item.external_uid}
    created = updated = deleted = unchanged = 0
    now = datetime.now(timezone.utc)

    for uid, payload in desired.items():
        event = by_uid.get(uid)
        if not event:
            db.add(CalendarEvent(family_id=family_id, calendar_id=calendar.id, title=payload["title"], description=payload["description"], starts_at=payload["starts_at"], ends_at=payload["ends_at"], all_day=True, category=payload["category"], external_uid=uid, source=SOURCE))
            created += 1
            continue
        changed = event.title != payload["title"] or event.description != payload["description"] or event.starts_at != payload["starts_at"] or event.ends_at != payload["ends_at"] or event.category != payload["category"] or event.deleted_at is not None
        if changed:
            event.title = payload["title"]
            event.description = payload["description"]
            event.starts_at = payload["starts_at"]
            event.ends_at = payload["ends_at"]
            event.all_day = True
            event.category = payload["category"]
            event.deleted_at = None
            event.updated_at = now
            updated += 1
        else:
            unchanged += 1

    wanted = set(desired)
    for event in existing:
        if event.external_uid and event.external_uid not in wanted and event.deleted_at is None:
            event.deleted_at = now
            event.updated_at = now
            deleted += 1

    db.commit()
    return {"created": created, "updated": updated, "deleted": deleted, "unchanged": unchanged}
