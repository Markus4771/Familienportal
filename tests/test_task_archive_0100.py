from datetime import datetime,timezone
from uuid import uuid4
from familienportal.task_models import FamilyTask

def test_new_task_is_not_archived():
    task=FamilyTask(id=uuid4(),title="Test")
    assert task.archived_at is None

def test_archive_timestamp_marks_task_archived():
    task=FamilyTask(id=uuid4(),title="Test")
    task.archived_at=datetime.now(timezone.utc)
    assert task.archived_at is not None

def test_restore_clears_archive_timestamp():
    task=FamilyTask(id=uuid4(),title="Test",archived_at=datetime.now(timezone.utc))
    task.archived_at=None
    assert task.archived_at is None
