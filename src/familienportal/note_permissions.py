from __future__ import annotations

from familienportal.models import User
from familienportal.note_models import FamilyNote
from familienportal.permissions import has_permission

NOTE_READ = "notes.read"
NOTE_CREATE = "notes.create"
NOTE_EDIT = "notes.edit"
NOTE_ARCHIVE = "notes.archive"
NOTE_DELETE = "notes.delete"
NOTE_SHARE = "notes.share"
NOTE_PRIVATE_READ = "notes.private.read"
NOTE_MANAGE = "notes.manage"


def same_family(user: User, note: FamilyNote) -> bool:
    return user.family_id == note.family_id


def is_owner(user: User, note: FamilyNote) -> bool:
    return note.owner_user_id == user.id


def can_read_note(user: User, note: FamilyNote) -> bool:
    if not same_family(user, note):
        return False
    if user.is_superadmin or has_permission(user, NOTE_MANAGE):
        return True
    if note.is_private:
        return is_owner(user, note) or has_permission(user, NOTE_PRIVATE_READ)
    return is_owner(user, note) or has_permission(user, NOTE_READ)


def can_create_note(user: User) -> bool:
    return user.is_superadmin or has_permission(user, NOTE_CREATE) or has_permission(user, NOTE_MANAGE)


def can_edit_note(user: User, note: FamilyNote) -> bool:
    if not same_family(user, note):
        return False
    return user.is_superadmin or has_permission(user, NOTE_MANAGE) or (
        is_owner(user, note) and has_permission(user, NOTE_EDIT)
    )


def can_archive_note(user: User, note: FamilyNote) -> bool:
    if not same_family(user, note):
        return False
    return user.is_superadmin or has_permission(user, NOTE_MANAGE) or (
        is_owner(user, note) and has_permission(user, NOTE_ARCHIVE)
    )


def can_share_note(user: User, note: FamilyNote) -> bool:
    if not same_family(user, note):
        return False
    return user.is_superadmin or has_permission(user, NOTE_MANAGE) or (
        is_owner(user, note) and has_permission(user, NOTE_SHARE)
    )


def can_delete_note(user: User, note: FamilyNote) -> bool:
    """Allow controlled deletion only after the note has been archived."""
    if not same_family(user, note) or note.archived_at is None:
        return False
    return user.is_superadmin or has_permission(user, NOTE_MANAGE) or (
        is_owner(user, note) and has_permission(user, NOTE_DELETE)
    )


def visible_notes(user: User, notes: list[FamilyNote]) -> list[FamilyNote]:
    return [note for note in notes if can_read_note(user, note)]
