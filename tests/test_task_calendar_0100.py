from datetime import datetime, timezone
from uuid import uuid4

from familienportal.task_calendar import DEFAULT_TASK_REMINDER_MINUTES, task_event_uid
from familienportal.task_models import FamilyTask


def test_task_event_uid_is_stable():
    task_id = uuid4()
    task = FamilyTask(id=task_id, title="Mülltonne")
    assert task_event_uid(task) == f"familienportal-task-{task_id}"


def test_default_task_reminder_is_one_hour():
    assert DEFAULT_TASK_REMINDER_MINUTES == 60


def test_due_task_can_carry_calendar_time():
    due = datetime(2026, 9, 20, 18, 30, tzinfo=timezone.utc)
    task = FamilyTask(id=uuid4(), title="Aufgabe", due_at=due)
    assert task.due_at == due
