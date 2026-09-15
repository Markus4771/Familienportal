from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from familienportal.calendar_models import CalendarEvent
from familienportal.database import Base
from familienportal.models import Family, User
from familienportal.task_calendar import DEFAULT_TASK_REMINDER_MINUTES, task_event_uid
from familienportal.task_models import FamilyTask, TaskStatus
from familienportal.task_service import archive_task, create_task, restore_task, set_status


def _database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _family_user(db: Session):
    family = Family(name="Integration", slug="integration")
    db.add(family)
    db.flush()
    user = User(family_id=family.id, email="integration@example.test", display_name="Integration", password_hash="x")
    db.add(user)
    db.commit()
    return family, user


def _event(db: Session, task: FamilyTask):
    return db.scalar(select(CalendarEvent).where(CalendarEvent.external_uid == task_event_uid(task)))


def test_task_calendar_lifecycle_create_complete_reopen_archive_restore():
    db = _database()
    family, user = _family_user(db)
    due = datetime(2026, 9, 20, 18, 0, tzinfo=timezone.utc)

    task = create_task(
        db,
        family_id=family.id,
        creator_user_id=user.id,
        title="Müll rausbringen",
        description="Gelbe Tonne",
        due_at=due,
    )
    event = _event(db, task)
    assert event is not None
    assert event.starts_at.replace(tzinfo=event.starts_at.tzinfo or timezone.utc) == due
    assert event.reminder_minutes == DEFAULT_TASK_REMINDER_MINUTES
    assert event.deleted_at is None

    set_status(db, task, TaskStatus.DONE.value)
    assert _event(db, task).deleted_at is not None

    set_status(db, task, TaskStatus.OPEN.value)
    assert _event(db, task).deleted_at is None

    archive_task(db, task)
    assert _event(db, task).deleted_at is not None

    restore_task(db, task)
    assert _event(db, task).deleted_at is None


def test_recurring_completion_creates_next_task_and_calendar_event():
    db = _database()
    family, user = _family_user(db)
    due = datetime(2026, 9, 20, 8, 0, tzinfo=timezone.utc)
    task = create_task(
        db,
        family_id=family.id,
        creator_user_id=user.id,
        title="Pflanzen gießen",
        due_at=due,
        recurrence="weekly",
        recurrence_interval=1,
    )

    set_status(db, task, TaskStatus.DONE.value)
    db.expire_all()
    tasks = db.scalars(select(FamilyTask).where(FamilyTask.family_id == family.id).order_by(FamilyTask.created_at)).all()
    assert len(tasks) == 2
    original, successor = tasks
    assert original.status == TaskStatus.DONE.value
    assert _event(db, original).deleted_at is not None
    assert successor.status == TaskStatus.OPEN.value
    assert successor.recurrence == "weekly"
    assert successor.due_at.replace(tzinfo=successor.due_at.tzinfo or timezone.utc) > due
    successor_event = _event(db, successor)
    assert successor_event is not None
    assert successor_event.deleted_at is None
    assert successor_event.reminder_minutes == DEFAULT_TASK_REMINDER_MINUTES


def test_task_without_due_date_has_no_calendar_event_until_due_date_is_added():
    db = _database()
    family, user = _family_user(db)
    task = create_task(db, family_id=family.id, creator_user_id=user.id, title="Ohne Termin")
    assert _event(db, task) is None
