from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from familienportal.task_models import FamilyTask


def aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def filter_tasks(tasks: list[FamilyTask], *, assignee_id: UUID | None = None, household_id: UUID | None = None, priority: str | None = None, due: str | None = None, now: datetime | None = None) -> list[FamilyTask]:
    now = now or datetime.now(timezone.utc)
    result = tasks
    if assignee_id:
        result = [task for task in result if task.assignee_user_id == assignee_id]
    if household_id:
        result = [task for task in result if task.household_id == household_id]
    if priority:
        result = [task for task in result if task.priority == priority]
    if due == "today":
        result = [task for task in result if aware(task.due_at) and aware(task.due_at).date() == now.date()]
    elif due == "week":
        until = now + timedelta(days=7)
        result = [task for task in result if aware(task.due_at) and now <= aware(task.due_at) <= until]
    elif due == "overdue":
        result = [task for task in result if aware(task.due_at) and aware(task.due_at) < now]
    elif due == "none":
        result = [task for task in result if task.due_at is None]
    return result


def presentation(task: FamilyTask, now: datetime | None = None) -> dict[str, bool]:
    now = now or datetime.now(timezone.utc)
    due = aware(task.due_at)
    return {
        "overdue": bool(due and due < now and task.status not in {"done", "cancelled"}),
        "urgent": task.priority == "urgent",
        "high": task.priority == "high",
    }
