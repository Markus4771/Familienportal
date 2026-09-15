from datetime import datetime, timezone

import pytest

from familienportal.task_models import FamilyTask, TaskPriority, TaskStatus
from familienportal.task_service import TaskValidationError, set_status


class FakeDb:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        pass


def task():
    return FamilyTask(title="Test", family_id=None, creator_user_id=None)


def test_set_done_sets_completion_time():
    db = FakeDb()
    item = task()
    set_status(db, item, TaskStatus.DONE.value)
    assert item.status == TaskStatus.DONE.value
    assert item.completed_at is not None
    assert item.completed_at.tzinfo is not None
    assert db.commits == 1


def test_reopen_clears_completion_time():
    db = FakeDb()
    item = task()
    item.status = TaskStatus.DONE.value
    item.completed_at = datetime.now(timezone.utc)
    set_status(db, item, TaskStatus.OPEN.value)
    assert item.status == TaskStatus.OPEN.value
    assert item.completed_at is None


def test_invalid_status_is_rejected():
    with pytest.raises(TaskValidationError):
        set_status(FakeDb(), task(), "invalid")


def test_task_defaults_are_defined():
    assert TaskPriority.NORMAL.value == "normal"
    assert TaskStatus.OPEN.value == "open"
