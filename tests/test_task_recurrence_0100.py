from datetime import datetime, timezone

from familienportal.task_models import FamilyTask
from familienportal.task_recurrence import next_due_at


def recurring(kind: str, interval: int, due: datetime) -> FamilyTask:
    return FamilyTask(title="Test", recurrence=kind, recurrence_interval=interval, due_at=due)


def test_daily_interval():
    due = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
    assert next_due_at(recurring("daily", 2, due), due).day == 17


def test_weekly_interval():
    due = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
    assert next_due_at(recurring("weekly", 2, due), due).day == 29


def test_month_end_is_clamped():
    due = datetime(2026, 1, 31, 18, 0, tzinfo=timezone.utc)
    result = next_due_at(recurring("monthly", 1, due), due)
    assert (result.month, result.day) == (2, 28)


def test_leap_day_yearly_is_clamped():
    due = datetime(2028, 2, 29, 12, 0, tzinfo=timezone.utc)
    result = next_due_at(recurring("yearly", 1, due), due)
    assert (result.year, result.month, result.day) == (2029, 2, 28)


def test_without_due_date_uses_completion_time():
    completed = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
    item = FamilyTask(title="Test", recurrence="daily", recurrence_interval=1, due_at=None)
    assert next_due_at(item, completed).day == 16
