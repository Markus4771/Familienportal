from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.models import Household, User, UserStatus
from familienportal.task_models import TaskPriority, TaskStatus
from familienportal.task_permissions import can_complete_task, can_create_task, can_delete_task, can_edit_task, can_read_task, visible_tasks
from familienportal.task_service import TaskValidationError, create_task, delete_task, get_task, list_tasks, set_status, update_task

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _user(request: Request, db: Session) -> User:
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    try:
        user = db.get(User, UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung") from exc
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    return user


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültige ID") from exc


def _parse_due(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges Fälligkeitsdatum") from exc


def _choices(db: Session, family_id: UUID):
    users = db.scalars(select(User).where(User.family_id == family_id, User.status == UserStatus.ACTIVE.value).order_by(User.display_name)).all()
    households = db.scalars(select(Household).where(Household.family_id == family_id).order_by(Household.name)).all()
    return users, households


@router.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request, view: str = "mine", db: Session = Depends(get_db)):
    user = _user(request, db)
    tasks = visible_tasks(user, list_tasks(db, user.family_id))
    now = datetime.now(timezone.utc)
    if view == "mine":
        tasks = [item for item in tasks if item.assignee_user_id == user.id or item.creator_user_id == user.id]
    elif view == "done":
        tasks = [item for item in tasks if item.status == TaskStatus.DONE.value]
    elif view == "overdue":
        tasks = [item for item in tasks if item.status not in {TaskStatus.DONE.value, TaskStatus.CANCELLED.value} and item.due_at and item.due_at.replace(tzinfo=item.due_at.tzinfo or timezone.utc) < now]
    elif view != "family":
        raise HTTPException(status_code=400, detail="Ungültige Ansicht")
    users, households = _choices(db, user.family_id)
    return templates.TemplateResponse(request=request, name="tasks.html", context={"user": user, "is_admin": user.is_superadmin, "tasks": tasks, "view": view, "users": users, "households": households, "can_create": can_create_task(user), "TaskStatus": TaskStatus})


@router.post("/tasks")
def task_create(request: Request, title: str = Form(...), description: str = Form(""), assignee_user_id: str = Form(""), household_id: str = Form(""), priority: str = Form("normal"), due_at: str = Form(""), is_private: bool = Form(False), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not can_create_task(user):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    try:
        create_task(db, family_id=user.family_id, creator_user_id=user.id, title=title, description=description, assignee_user_id=_parse_uuid(assignee_user_id), household_id=_parse_uuid(household_id), priority=priority, due_at=_parse_due(due_at), is_private=is_private)
    except TaskValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/tasks", status_code=303)


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def task_edit_page(request: Request, task_id: UUID, db: Session = Depends(get_db)):
    user = _user(request, db)
    task = get_task(db, user.family_id, task_id)
    if not task or not can_read_task(user, task):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    if not can_edit_task(user, task):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    users, households = _choices(db, user.family_id)
    return templates.TemplateResponse(request=request, name="task_edit.html", context={"user": user, "is_admin": user.is_superadmin, "task": task, "users": users, "households": households})


@router.post("/tasks/{task_id}/edit")
def task_edit(request: Request, task_id: UUID, title: str = Form(...), description: str = Form(""), assignee_user_id: str = Form(""), household_id: str = Form(""), priority: str = Form("normal"), due_at: str = Form(""), recurrence: str = Form(""), recurrence_interval: int = Form(1), is_private: bool = Form(False), db: Session = Depends(get_db)):
    user = _user(request, db)
    task = get_task(db, user.family_id, task_id)
    if not task or not can_edit_task(user, task):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    try:
        update_task(db, task, title=title, description=description, assignee_user_id=_parse_uuid(assignee_user_id), household_id=_parse_uuid(household_id), priority=priority, due_at=_parse_due(due_at), recurrence=recurrence or None, recurrence_interval=recurrence_interval, is_private=is_private)
    except TaskValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/tasks", status_code=303)


@router.post("/tasks/{task_id}/status")
def task_status(request: Request, task_id: UUID, status: str = Form(...), db: Session = Depends(get_db)):
    user = _user(request, db)
    task = get_task(db, user.family_id, task_id)
    if not task or not can_complete_task(user, task):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    try:
        set_status(db, task, status)
    except TaskValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse("/tasks", status_code=303)


@router.post("/tasks/{task_id}/delete")
def task_delete(request: Request, task_id: UUID, db: Session = Depends(get_db)):
    user = _user(request, db)
    task = get_task(db, user.family_id, task_id)
    if not task or not can_delete_task(user, task):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    delete_task(db, task)
    return RedirectResponse("/tasks", status_code=303)
