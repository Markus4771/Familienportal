from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.calendar_models import Calendar, CalendarEvent
from familienportal.task_models import FamilyTask, TaskStatus

TASK_CALENDAR_SLUG = "aufgaben"
TASK_CALENDAR_NAME = "Aufgaben"
DEFAULT_TASK_REMINDER_MINUTES = 60


def ensure_task_calendar(db: Session, family_id):
    calendar = db.scalar(select(Calendar).where(Calendar.family_id == family_id, Calendar.slug == TASK_CALENDAR_SLUG))
    if calendar:
        return calendar
    calendar = Calendar(family_id=family_id, name=TASK_CALENDAR_NAME, slug=TASK_CALENDAR_SLUG, kind="tasks", description="Fällige Familienaufgaben")
    db.add(calendar)
    db.flush()
    return calendar


def task_event_uid(task: FamilyTask) -> str:
    return f"familienportal-task-{task.id}"


def sync_task_event(db: Session, task: FamilyTask, reminder_minutes: int = DEFAULT_TASK_REMINDER_MINUTES) -> CalendarEvent | None:
    uid = task_event_uid(task)
    event = db.scalar(select(CalendarEvent).where(CalendarEvent.family_id == task.family_id, CalendarEvent.external_uid == uid, CalendarEvent.source == "tasks"))
    active = task.due_at is not None and task.status not in {TaskStatus.DONE.value, TaskStatus.CANCELLED.value}
    if not active:
        if event and event.deleted_at is None:
            from datetime import datetime, timezone
            event.deleted_at = datetime.now(timezone.utc)
        return event
    calendar = ensure_task_calendar(db, task.family_id)
    starts = task.due_at
    ends = starts + timedelta(minutes=30)
    if event is None:
        event = CalendarEvent(family_id=task.family_id, calendar_id=calendar.id, created_by_user_id=task.creator_user_id, title=f"Aufgabe: {task.title}", starts_at=starts, ends_at=ends, category="task", external_uid=uid, source="tasks")
        db.add(event)
    event.calendar_id = calendar.id
    event.title = f"Aufgabe: {task.title}"
    event.description = task.description
    event.starts_at = starts
    event.ends_at = ends
    event.reminder_minutes = max(0, reminder_minutes)
    event.deleted_at = None
    return event


def remove_task_event(db: Session, task: FamilyTask) -> None:
    sync_task_event(db, task)
