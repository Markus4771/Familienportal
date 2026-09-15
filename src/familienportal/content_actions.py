from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.content_link_service import create_link
from familienportal.list_models import FamilyList
from familienportal.note_models import FamilyNote
from familienportal.task_service import create_task


def create_task_from_content(db: Session, actor, *, note: FamilyNote | None = None, family_list: FamilyList | None = None, due_at: datetime | None = None):
    source = note or family_list
    if source is None or actor.family_id != source.family_id:
        raise ValueError("invalid content source")
    task = create_task(db, family_id=actor.family_id, creator_user_id=actor.id, title=source.title, description=getattr(source, "content", None) or getattr(source, "description", None), household_id=source.household_id, due_at=due_at, is_private=source.is_private, commit=False)
    create_link(db, actor, note=note, family_list=family_list, task=task)
    return task


def create_event_from_content(db: Session, actor, *, starts_at: datetime, note: FamilyNote | None = None, family_list: FamilyList | None = None):
    source = note or family_list
    if source is None or actor.family_id != source.family_id:
        raise ValueError("invalid content source")
    calendar = db.scalar(select(Calendar).where(Calendar.family_id == actor.family_id, Calendar.slug == "familie"))
    if calendar is None:
        calendar = db.scalar(select(Calendar).where(Calendar.family_id == actor.family_id).order_by(Calendar.created_at))
    if calendar is None:
        raise ValueError("no calendar available")
    event = CalendarEvent(family_id=actor.family_id, calendar_id=calendar.id, created_by_user_id=actor.id, title=source.title, description=getattr(source, "content", None) or getattr(source, "description", None), starts_at=starts_at, ends_at=starts_at + timedelta(hours=1), category="family")
    db.add(event); db.flush()
    create_link(db, actor, note=note, family_list=family_list, event=event)
    return event
