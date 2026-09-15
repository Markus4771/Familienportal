from datetime import datetime, timezone
from uuid import uuid4

from familienportal.task_calendar import (
    DEFAULT_TASK_REMINDER_MINUTES,
    task_event_uid,
    task_has_active_calendar_event,
)
from familienportal.task_models import FamilyTask, TaskStatus


def due_task() -> FamilyTask:
    return FamilyTask(
        id=uuid4(),
        title="Aufgabe",
        due_at=datetime(2026, 9, 20, 18, 30, tzinfo=timezone.utc),
        status=TaskStatus.OPEN.value,
    )


def test_task_event_uid_is_stable():
    task_id = uuid4()
    task = FamilyTask(id=task_id, title="Mülltonne")
    assert task_event_uid(task) == f"familienportal-task-{task_id}"


def test_default_task_reminder_is_one_hour():
    assert DEFAULT_TASK_REMINDER_MINUTES == 60


def test_due_task_can_carry_calendar_time():
    task = due_task()
    assert task.due_at == datetime(2026, 9, 20, 18, 30, tzinfo=timezone.utc)


def test_open_due_task_has_active_calendar_event():
    assert task_has_active_calendar_event(due_task()) is True


def test_archived_task_has_no_active_calendar_event():
    task = due_task()
    task.archived_at = datetime.now(timezone.utc)
    assert task_has_active_calendar_event(task) is False


def test_done_or_cancelled_task_has_no_active_calendar_event():
    task = due_task()
    task.status = TaskStatus.DONE.value
    assert task_has_active_calendar_event(task) is False
    task.status = TaskStatus.CANCELLED.value
    assert task_has_active_calendar_event(task) is False


def test_task_without_due_date_has_no_active_calendar_event():
    task = due_task()
    task.due_at = None
    assert task_has_active_calendar_event(task) is False
