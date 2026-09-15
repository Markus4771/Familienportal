from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.calendar_models import CalendarEvent
from familienportal.content_links import ContentLink, ContentLinkKind
from familienportal.list_models import FamilyList
from familienportal.note_models import FamilyNote
from familienportal.task_models import FamilyTask


def _kind(note, family_list, task, event) -> ContentLinkKind:
    if note is not None and task is not None: return ContentLinkKind.NOTE_TASK
    if note is not None and event is not None: return ContentLinkKind.NOTE_EVENT
    if family_list is not None and task is not None: return ContentLinkKind.LIST_TASK
    if family_list is not None and event is not None: return ContentLinkKind.LIST_EVENT
    raise ValueError("exactly one source and one target required")


def create_link(db: Session, actor, *, note: FamilyNote | None = None, family_list: FamilyList | None = None, task: FamilyTask | None = None, event: CalendarEvent | None = None) -> ContentLink:
    kind = _kind(note, family_list, task, event)
    objects = [obj for obj in (note, family_list, task, event) if obj is not None]
    if any(obj.family_id != actor.family_id for obj in objects):
        raise ValueError("family boundary violation")
    filters = [ContentLink.family_id == actor.family_id, ContentLink.kind == kind.value]
    filters += [ContentLink.note_id == (note.id if note else None), ContentLink.list_id == (family_list.id if family_list else None), ContentLink.task_id == (task.id if task else None), ContentLink.event_id == (event.id if event else None)]
    existing = db.scalar(select(ContentLink).where(*filters))
    if existing:
        return existing
    link = ContentLink(family_id=actor.family_id, kind=kind.value, note_id=note.id if note else None, list_id=family_list.id if family_list else None, task_id=task.id if task else None, event_id=event.id if event else None, created_by_user_id=actor.id)
    db.add(link)
    return link


def links_for_note(db: Session, note: FamilyNote) -> list[ContentLink]:
    return list(db.scalars(select(ContentLink).where(ContentLink.family_id == note.family_id, ContentLink.note_id == note.id).order_by(ContentLink.created_at.desc())))


def links_for_list(db: Session, family_list: FamilyList) -> list[ContentLink]:
    return list(db.scalars(select(ContentLink).where(ContentLink.family_id == family_list.family_id, ContentLink.list_id == family_list.id).order_by(ContentLink.created_at.desc())))
