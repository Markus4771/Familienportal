from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.list_models import FamilyList, FamilyListItem
from familienportal.list_permissions import can_read_list
from familienportal.models import User
from familienportal.note_models import FamilyNote
from familienportal.note_permissions import can_read_note


def content_dashboard(db: Session, user: User) -> dict[str, object]:
    notes = list(db.scalars(select(FamilyNote).where(FamilyNote.family_id == user.family_id, FamilyNote.archived_at.is_(None))))
    visible_notes = [note for note in notes if can_read_note(user, note)]

    lists = list(db.scalars(select(FamilyList).where(FamilyList.family_id == user.family_id, FamilyList.archived_at.is_(None))))
    visible_lists = [family_list for family_list in lists if can_read_list(user, family_list)]
    visible_list_ids = [family_list.id for family_list in visible_lists]

    open_items = 0
    if visible_list_ids:
        open_items = int(db.scalar(select(func.count(FamilyListItem.id)).where(FamilyListItem.list_id.in_(visible_list_ids), FamilyListItem.is_done.is_(False))) or 0)

    recent_notes = sorted(visible_notes, key=lambda note: note.updated_at, reverse=True)[:5]
    return {
        "notes_count": len(visible_notes),
        "lists_count": len(visible_lists),
        "open_list_items": open_items,
        "recent_notes": recent_notes,
    }
