from __future__ import annotations

from familienportal.list_models import FamilyList
from familienportal.models import User
from familienportal.permissions import has_permission

LIST_READ = "lists.read"
LIST_CREATE = "lists.create"
LIST_EDIT = "lists.edit"
LIST_ASSIGN = "lists.assign"
LIST_ARCHIVE = "lists.archive"
LIST_DELETE = "lists.delete"
LIST_PRIVATE_READ = "lists.private.read"
LIST_MANAGE = "lists.manage"


def same_family(user: User, family_list: FamilyList) -> bool:
    return user.family_id == family_list.family_id


def is_owner(user: User, family_list: FamilyList) -> bool:
    return family_list.owner_user_id == user.id


def can_read_list(user: User, family_list: FamilyList) -> bool:
    if not same_family(user, family_list):
        return False
    if user.is_superadmin or has_permission(user, LIST_MANAGE):
        return True
    if family_list.is_private:
        return is_owner(user, family_list) or has_permission(user, LIST_PRIVATE_READ)
    return is_owner(user, family_list) or has_permission(user, LIST_READ)


def can_create_list(user: User) -> bool:
    return user.is_superadmin or has_permission(user, LIST_CREATE) or has_permission(user, LIST_MANAGE)


def can_edit_list(user: User, family_list: FamilyList) -> bool:
    if not same_family(user, family_list):
        return False
    return user.is_superadmin or has_permission(user, LIST_MANAGE) or (
        is_owner(user, family_list) and has_permission(user, LIST_EDIT)
    )


def can_assign_list_items(user: User, family_list: FamilyList) -> bool:
    if not same_family(user, family_list):
        return False
    return user.is_superadmin or has_permission(user, LIST_MANAGE) or has_permission(user, LIST_ASSIGN)


def can_archive_list(user: User, family_list: FamilyList) -> bool:
    if not same_family(user, family_list):
        return False
    return user.is_superadmin or has_permission(user, LIST_MANAGE) or (
        is_owner(user, family_list) and has_permission(user, LIST_ARCHIVE)
    )


def can_delete_list(user: User, family_list: FamilyList) -> bool:
    if not same_family(user, family_list) or family_list.archived_at is None:
        return False
    return user.is_superadmin or has_permission(user, LIST_MANAGE) or (
        is_owner(user, family_list) and has_permission(user, LIST_DELETE)
    )
