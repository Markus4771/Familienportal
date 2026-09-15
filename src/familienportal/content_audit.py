from __future__ import annotations

import json

from sqlalchemy.orm import Session

from familienportal.list_models import FamilyList, FamilyListItem
from familienportal.models import AuditEvent, User
from familienportal.note_models import FamilyNote


def _event(db: Session, actor: User, action: str, target_type: str, target_id: str, details: dict[str, object]) -> AuditEvent:
    event = AuditEvent(
        family_id=actor.family_id,
        actor_user_id=actor.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details, ensure_ascii=False, default=str),
    )
    db.add(event)
    return event


def audit_note(db: Session, action: str, actor: User, note: FamilyNote, **details: object) -> AuditEvent:
    """Never put note title/content into audit metadata, especially for private notes."""
    safe = {
        "household_id": str(note.household_id) if note.household_id else None,
        "owner_user_id": str(note.owner_user_id) if note.owner_user_id else None,
        "is_private": bool(note.is_private),
        "archived": note.archived_at is not None,
        **details,
    }
    return _event(db, actor, action, "family_note", str(note.id), safe)


def audit_list(db: Session, action: str, actor: User, family_list: FamilyList, **details: object) -> AuditEvent:
    safe = {
        "kind": family_list.kind,
        "household_id": str(family_list.household_id) if family_list.household_id else None,
        "owner_user_id": str(family_list.owner_user_id) if family_list.owner_user_id else None,
        "is_private": bool(family_list.is_private),
        "archived": family_list.archived_at is not None,
        **details,
    }
    return _event(db, actor, action, "family_list", str(family_list.id), safe)


def audit_list_item(db: Session, action: str, actor: User, item: FamilyListItem, **details: object) -> AuditEvent:
    safe = {
        "list_id": str(item.list_id),
        "assignee_user_id": str(item.assignee_user_id) if item.assignee_user_id else None,
        "is_done": bool(item.is_done),
        **details,
    }
    return _event(db, actor, action, "family_list_item", str(item.id), safe)
