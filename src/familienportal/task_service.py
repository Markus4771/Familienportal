from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.models import Household, User
from familienportal.task_models import FamilyTask, TaskPriority, TaskStatus
from familienportal.task_recurrence import next_due_at

VALID_STATUSES = {item.value for item in TaskStatus}
VALID_PRIORITIES = {item.value for item in TaskPriority}
VALID_RECURRENCES = {None, "daily", "weekly", "monthly", "yearly"}

class TaskValidationError(ValueError):
    pass

def _clean_title(value: str) -> str:
    title = value.strip()
    if not title:
        raise TaskValidationError("Titel darf nicht leer sein.")
    if len(title) > 240:
        raise TaskValidationError("Titel darf maximal 240 Zeichen enthalten.")
    return title

def _clean_description(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None

def _family_user(db: Session, family_id: UUID, user_id: UUID | None) -> UUID | None:
    if user_id is None:
        return None
    if db.scalar(select(User.id).where(User.id == user_id, User.family_id == family_id)) is None:
        raise TaskValidationError("Zugewiesener Benutzer gehört nicht zu dieser Familie.")
    return user_id

def _family_household(db: Session, family_id: UUID, household_id: UUID | None) -> UUID | None:
    if household_id is None:
        return None
    if db.scalar(select(Household.id).where(Household.id == household_id, Household.family_id == family_id)) is None:
        raise TaskValidationError("Haushalt gehört nicht zu dieser Familie.")
    return household_id

def get_task(db: Session, family_id: UUID, task_id: UUID) -> FamilyTask | None:
    return db.scalar(select(FamilyTask).where(FamilyTask.id == task_id, FamilyTask.family_id == family_id))

def list_tasks(db: Session, family_id: UUID, *, status: str | None = None, assignee_user_id: UUID | None = None) -> list[FamilyTask]:
    query = select(FamilyTask).where(FamilyTask.family_id == family_id)
    if status:
        if status not in VALID_STATUSES:
            raise TaskValidationError("Ungültiger Aufgabenstatus.")
        query = query.where(FamilyTask.status == status)
    if assignee_user_id:
        query = query.where(FamilyTask.assignee_user_id == assignee_user_id)
    return list(db.scalars(query.order_by(FamilyTask.due_at.asc().nullslast(), FamilyTask.created_at.desc())).all())

def create_task(db: Session, *, family_id: UUID, creator_user_id: UUID, title: str, description: str | None = None, household_id: UUID | None = None, assignee_user_id: UUID | None = None, priority: str = TaskPriority.NORMAL.value, due_at: datetime | None = None, recurrence: str | None = None, recurrence_interval: int = 1, is_private: bool = False) -> FamilyTask:
    if priority not in VALID_PRIORITIES:
        raise TaskValidationError("Ungültige Priorität.")
    if recurrence not in VALID_RECURRENCES:
        raise TaskValidationError("Ungültige Wiederholung.")
    if recurrence_interval < 1 or recurrence_interval > 365:
        raise TaskValidationError("Wiederholungsintervall muss zwischen 1 und 365 liegen.")
    task = FamilyTask(family_id=family_id, creator_user_id=_family_user(db, family_id, creator_user_id), household_id=_family_household(db, family_id, household_id), assignee_user_id=_family_user(db, family_id, assignee_user_id), title=_clean_title(title), description=_clean_description(description), priority=priority, due_at=due_at, recurrence=recurrence, recurrence_interval=recurrence_interval, is_private=is_private)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def update_task(db: Session, task: FamilyTask, *, title: str, description: str | None, household_id: UUID | None, assignee_user_id: UUID | None, priority: str, due_at: datetime | None, recurrence: str | None, recurrence_interval: int, is_private: bool) -> FamilyTask:
    if priority not in VALID_PRIORITIES:
        raise TaskValidationError("Ungültige Priorität.")
    if recurrence not in VALID_RECURRENCES:
        raise TaskValidationError("Ungültige Wiederholung.")
    if recurrence_interval < 1 or recurrence_interval > 365:
        raise TaskValidationError("Wiederholungsintervall muss zwischen 1 und 365 liegen.")
    task.title = _clean_title(title)
    task.description = _clean_description(description)
    task.household_id = _family_household(db, task.family_id, household_id)
    task.assignee_user_id = _family_user(db, task.family_id, assignee_user_id)
    task.priority = priority
    task.due_at = due_at
    task.recurrence = recurrence
    task.recurrence_interval = recurrence_interval
    task.is_private = is_private
    db.commit()
    db.refresh(task)
    return task

def _next_recurring_task(task: FamilyTask, completed_at: datetime) -> FamilyTask | None:
    due_at = next_due_at(task, completed_at)
    if due_at is None:
        return None
    return FamilyTask(family_id=task.family_id, household_id=task.household_id, creator_user_id=task.creator_user_id, assignee_user_id=task.assignee_user_id, title=task.title, description=task.description, status=TaskStatus.OPEN.value, priority=task.priority, due_at=due_at, recurrence=task.recurrence, recurrence_interval=task.recurrence_interval, is_private=task.is_private)

def set_status(db: Session, task: FamilyTask, status: str) -> FamilyTask:
    if status not in VALID_STATUSES:
        raise TaskValidationError("Ungültiger Aufgabenstatus.")
    was_done = task.status == TaskStatus.DONE.value
    task.status = status
    task.completed_at = datetime.now(timezone.utc) if status == TaskStatus.DONE.value else None
    if status == TaskStatus.DONE.value and not was_done and task.recurrence:
        successor = _next_recurring_task(task, task.completed_at)
        if successor is not None:
            db.add(successor)
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task: FamilyTask) -> None:
    db.delete(task)
    db.commit()
