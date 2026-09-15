from __future__ import annotations

import calendar
from datetime import datetime, timedelta

from familienportal.task_models import FamilyTask


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def next_due_at(task: FamilyTask, completed_at: datetime) -> datetime | None:
    if not task.recurrence:
        return None
    interval = max(1, task.recurrence_interval or 1)
    base = task.due_at or completed_at
    if task.recurrence == "daily":
        return base + timedelta(days=interval)
    if task.recurrence == "weekly":
        return base + timedelta(weeks=interval)
    if task.recurrence == "monthly":
        return _add_months(base, interval)
    if task.recurrence == "yearly":
        return _add_months(base, interval * 12)
    return None
