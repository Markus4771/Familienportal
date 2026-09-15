from __future__ import annotations

from datetime import datetime, timezone

from familienportal.models import User
from familienportal.task_models import TaskStatus
from familienportal.task_permissions import can_complete_task, visible_tasks
from familienportal.task_service import list_tasks


def _aware(value):
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def task_dashboard(db, user: User, limit: int = 5) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    tasks = visible_tasks(user, list_tasks(db, user.family_id))
    active = [item for item in tasks if item.status not in {TaskStatus.DONE.value, TaskStatus.CANCELLED.value}]
    mine = [item for item in active if item.assignee_user_id == user.id or item.creator_user_id == user.id]
    overdue = sorted(
        [item for item in mine if item.due_at and _aware(item.due_at) < now],
        key=lambda item: _aware(item.due_at),
    )
    today = sorted(
        [item for item in mine if item.due_at and _aware(item.due_at).date() == now.date() and _aware(item.due_at) >= now],
        key=lambda item: _aware(item.due_at),
    )
    upcoming = sorted(
        [item for item in mine if item.due_at and _aware(item.due_at) > now],
        key=lambda item: _aware(item.due_at),
    )[:limit]
    completable_ids = {str(item.id) for item in mine if can_complete_task(user, item)}
    return {
        "open_count": len(mine),
        "overdue_count": len(overdue),
        "today_count": len(today),
        "overdue": overdue[:limit],
        "today": today[:limit],
        "upcoming": upcoming,
        "completable_ids": completable_ids,
    }
