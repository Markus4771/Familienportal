from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch

from familienportal.models import Role, User
from familienportal.task_dashboard import task_dashboard
from familienportal.task_models import FamilyTask, TaskStatus


def make_user(*permissions):
    family_id = uuid4()
    user = User(id=uuid4(), family_id=family_id, email="dashboard@example.test", display_name="Dashboard", password_hash="x")
    user.roles = [Role(id=uuid4(), family_id=family_id, name="Test", permissions=",".join(permissions))]
    return user


def make_task(user, due_at, status=TaskStatus.OPEN.value):
    return FamilyTask(id=uuid4(), family_id=user.family_id, creator_user_id=user.id, assignee_user_id=user.id, title="Test", due_at=due_at, status=status)


def test_dashboard_separates_overdue_today_and_upcoming():
    user = make_user("tasks.read", "tasks.complete")
    now = datetime.now(timezone.utc)
    overdue = make_task(user, now - timedelta(hours=2))
    today = make_task(user, now + timedelta(minutes=30))
    tomorrow = make_task(user, now + timedelta(days=1))
    done = make_task(user, now + timedelta(minutes=10), TaskStatus.DONE.value)
    with patch("familienportal.task_dashboard.list_tasks", return_value=[overdue, today, tomorrow, done]):
        result = task_dashboard(None, user)
    assert result["open_count"] == 3
    assert result["overdue_count"] == 1
    assert result["today_count"] == 1
    assert result["overdue"] == [overdue]
    assert result["today"] == [today]
    assert tomorrow in result["upcoming"]
    assert str(overdue.id) in result["completable_ids"]


def test_dashboard_hides_quick_complete_without_permission():
    user = make_user("tasks.read")
    task = make_task(user, datetime.now(timezone.utc) + timedelta(hours=1))
    with patch("familienportal.task_dashboard.list_tasks", return_value=[task]):
        result = task_dashboard(None, user)
    assert str(task.id) not in result["completable_ids"]
