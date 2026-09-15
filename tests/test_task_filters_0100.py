from datetime import datetime, timedelta, timezone
from uuid import uuid4
from familienportal.task_filters import filter_tasks, presentation
from familienportal.task_models import FamilyTask

def item(**kw): return FamilyTask(id=uuid4(),title="Test",**kw)

def test_filter_by_assignee_household_and_priority():
    user_id=uuid4(); household_id=uuid4(); tasks=[item(assignee_user_id=user_id,household_id=household_id,priority="urgent"),item(priority="normal")]
    assert len(filter_tasks(tasks,assignee_id=user_id,household_id=household_id,priority="urgent"))==1

def test_today_and_week_filters():
    now=datetime(2026,9,15,10,tzinfo=timezone.utc); tasks=[item(due_at=now+timedelta(hours=2)),item(due_at=now+timedelta(days=3)),item(due_at=now+timedelta(days=10))]
    assert len(filter_tasks(tasks,due="today",now=now))==1
    assert len(filter_tasks(tasks,due="week",now=now))==2

def test_overdue_and_urgent_presentation():
    now=datetime(2026,9,15,10,tzinfo=timezone.utc); task=item(due_at=now-timedelta(hours=1),priority="urgent",status="open")
    flags=presentation(task,now); assert flags["overdue"] is True; assert flags["urgent"] is True
