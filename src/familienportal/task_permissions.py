from __future__ import annotations

from familienportal.models import User
from familienportal.permissions import has_permission
from familienportal.task_models import FamilyTask

TASK_READ = "tasks.read"
TASK_CREATE = "tasks.create"
TASK_EDIT = "tasks.edit"
TASK_ASSIGN = "tasks.assign"
TASK_DELETE = "tasks.delete"
TASK_COMPLETE = "tasks.complete"
TASK_PRIVATE_READ = "tasks.private.read"
TASK_MANAGE = "tasks.manage"


def same_family(user: User, task: FamilyTask) -> bool:
    return user.family_id == task.family_id


def is_owner(user: User, task: FamilyTask) -> bool:
    return task.creator_user_id == user.id


def is_assignee(user: User, task: FamilyTask) -> bool:
    return task.assignee_user_id == user.id


def can_read_task(user: User, task: FamilyTask) -> bool:
    if not same_family(user, task):
        return False
    if user.is_superadmin or has_permission(user, TASK_MANAGE):
        return True
    if task.is_private:
        return is_owner(user, task) or is_assignee(user, task) or has_permission(user, TASK_PRIVATE_READ)
    return is_owner(user, task) or is_assignee(user, task) or has_permission(user, TASK_READ)


def can_create_task(user: User) -> bool:
    return user.is_superadmin or has_permission(user, TASK_CREATE) or has_permission(user, TASK_MANAGE)


def can_edit_task(user: User, task: FamilyTask) -> bool:
    if not same_family(user, task):
        return False
    return user.is_superadmin or has_permission(user, TASK_MANAGE) or (is_owner(user, task) and has_permission(user, TASK_EDIT))


def can_assign_task(user: User, task: FamilyTask | None = None) -> bool:
    if task is not None and not same_family(user, task):
        return False
    return user.is_superadmin or has_permission(user, TASK_ASSIGN) or has_permission(user, TASK_MANAGE)


def can_complete_task(user: User, task: FamilyTask) -> bool:
    if not same_family(user, task):
        return False
    return (
        user.is_superadmin
        or has_permission(user, TASK_MANAGE)
        or has_permission(user, TASK_COMPLETE)
        and (is_owner(user, task) or is_assignee(user, task))
    )


def can_delete_task(user: User, task: FamilyTask) -> bool:
    if not same_family(user, task):
        return False
    return user.is_superadmin or has_permission(user, TASK_MANAGE) or (is_owner(user, task) and has_permission(user, TASK_DELETE))


def visible_tasks(user: User, tasks: list[FamilyTask]) -> list[FamilyTask]:
    return [task for task in tasks if can_read_task(user, task)]
