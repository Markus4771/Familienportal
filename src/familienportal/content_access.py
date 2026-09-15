from __future__ import annotations

from sqlalchemy.orm import Session

from familienportal.content_audit import audit_list, audit_note
from familienportal.content_sharing import list_shared_with, note_shared_with
from familienportal.list_models import FamilyList
from familienportal.list_permissions import can_read_list, is_owner as is_list_owner
from familienportal.models import User
from familienportal.note_models import FamilyNote
from familienportal.note_permissions import can_read_note, is_owner as is_note_owner


def can_access_note(db: Session, user: User, note: FamilyNote, *, audit_admin: bool = False) -> bool:
    allowed = can_read_note(user, note) or note_shared_with(db, user, note)
    if allowed and audit_admin and note.is_private and not is_note_owner(user, note) and not note_shared_with(db, user, note):
        audit_note(db, "note.private_access", user, note, access="administrative")
    return allowed


def can_access_list(db: Session, user: User, family_list: FamilyList, *, audit_admin: bool = False) -> bool:
    allowed = can_read_list(user, family_list) or list_shared_with(db, user, family_list)
    if allowed and audit_admin and family_list.is_private and not is_list_owner(user, family_list) and not list_shared_with(db, user, family_list):
        audit_list(db, "list.private_access", user, family_list, access="administrative")
    return allowed
