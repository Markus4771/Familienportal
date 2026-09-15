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
from familienportal.task_audit import audit_task
from familienportal.task_filters import filter_tasks, presentation
from familienportal.task_models import TaskStatus
from familienportal.task_permissions import can_complete_task, can_create_task, can_delete_task, can_edit_task, can_read_task, visible_tasks
from familienportal.task_service import TaskValidationError, create_task, delete_task, get_task, list_tasks, set_status, update_task

router=APIRouter(include_in_schema=False); templates=Jinja2Templates(directory="src/familienportal/templates")
def _user(request,db):
    value=request.session.get("user_id")
    if not value: raise HTTPException(401,"Anmeldung erforderlich")
    try:user=db.get(User,UUID(value))
    except ValueError as exc: raise HTTPException(401,"Ungültige Sitzung") from exc
    if not user or user.status!=UserStatus.ACTIVE.value: raise HTTPException(401,"Anmeldung erforderlich")
    return user
def _uuid(value):
    if not value:return None
    try:return UUID(value)
    except ValueError as exc:raise HTTPException(400,"Ungültige ID") from exc
def _due(value):
    if not value:return None
    try:return datetime.fromisoformat(value)
    except ValueError as exc:raise HTTPException(400,"Ungültiges Fälligkeitsdatum") from exc
def _choices(db,fid):
    return (db.scalars(select(User).where(User.family_id==fid,User.status==UserStatus.ACTIVE.value).order_by(User.display_name)).all(),db.scalars(select(Household).where(Household.family_id==fid).order_by(Household.name)).all())

@router.get("/tasks",response_class=HTMLResponse)
def tasks_page(request:Request,view:str="mine",assignee:str="",household:str="",priority:str="",due:str="",db:Session=Depends(get_db)):
    user=_user(request,db); tasks=visible_tasks(user,list_tasks(db,user.family_id)); now=datetime.now(timezone.utc)
    if view=="mine":tasks=[i for i in tasks if i.assignee_user_id==user.id or i.creator_user_id==user.id]
    elif view=="done":tasks=[i for i in tasks if i.status==TaskStatus.DONE.value]
    elif view=="overdue":tasks=[i for i in tasks if i.status not in {TaskStatus.DONE.value,TaskStatus.CANCELLED.value} and i.due_at and i.due_at.replace(tzinfo=i.due_at.tzinfo or timezone.utc)<now]
    elif view!="family":raise HTTPException(400,"Ungültige Ansicht")
    tasks=filter_tasks(tasks,assignee_id=_uuid(assignee),household_id=_uuid(household),priority=priority or None,due=due or None,now=now)
    users,households=_choices(db,user.family_id)
    flags={str(i.id):presentation(i,now) for i in tasks}
    return templates.TemplateResponse(request=request,name="tasks.html",context={"user":user,"is_admin":user.is_superadmin,"tasks":tasks,"view":view,"users":users,"households":households,"can_create":can_create_task(user),"TaskStatus":TaskStatus,"flags":flags,"filters":{"assignee":assignee,"household":household,"priority":priority,"due":due}})

@router.post("/tasks")
def task_create(request:Request,title:str=Form(...),description:str=Form(""),assignee_user_id:str=Form(""),household_id:str=Form(""),priority:str=Form("normal"),due_at:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db)
    if not can_create_task(user):raise HTTPException(403,"Keine Berechtigung")
    try:task=create_task(db,family_id=user.family_id,creator_user_id=user.id,title=title,description=description,assignee_user_id=_uuid(assignee_user_id),household_id=_uuid(household_id),priority=priority,due_at=_due(due_at),is_private=is_private);audit_task(db,"task.created",user,task);db.commit()
    except TaskValidationError as exc:raise HTTPException(400,str(exc)) from exc
    return RedirectResponse("/tasks",303)

@router.get("/tasks/{task_id}/edit",response_class=HTMLResponse)
def task_edit_page(request:Request,task_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);task=get_task(db,user.family_id,task_id)
    if not task or not can_read_task(user,task):raise HTTPException(404,"Aufgabe nicht gefunden")
    if not can_edit_task(user,task):raise HTTPException(403,"Keine Berechtigung")
    users,households=_choices(db,user.family_id);return templates.TemplateResponse(request=request,name="task_edit.html",context={"user":user,"is_admin":user.is_superadmin,"task":task,"users":users,"households":households})

@router.post("/tasks/{task_id}/edit")
def task_edit(request:Request,task_id:UUID,title:str=Form(...),description:str=Form(""),assignee_user_id:str=Form(""),household_id:str=Form(""),priority:str=Form("normal"),due_at:str=Form(""),recurrence:str=Form(""),recurrence_interval:int=Form(1),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db);task=get_task(db,user.family_id,task_id)
    if not task or not can_edit_task(user,task):raise HTTPException(404,"Aufgabe nicht gefunden")
    old=task.assignee_user_id
    try:update_task(db,task,title=title,description=description,assignee_user_id=_uuid(assignee_user_id),household_id=_uuid(household_id),priority=priority,due_at=_due(due_at),recurrence=recurrence or None,recurrence_interval=recurrence_interval,is_private=is_private);audit_task(db,"task.updated",user,task);audit_task(db,"task.assigned",user,task,previous_assignee_user_id=str(old) if old else None) if old!=task.assignee_user_id else None;db.commit()
    except TaskValidationError as exc:raise HTTPException(400,str(exc)) from exc
    return RedirectResponse("/tasks",303)

@router.post("/tasks/{task_id}/status")
def task_status(request:Request,task_id:UUID,status:str=Form(...),db:Session=Depends(get_db)):
    user=_user(request,db);task=get_task(db,user.family_id,task_id)
    if not task or not can_complete_task(user,task):raise HTTPException(404,"Aufgabe nicht gefunden")
    previous=task.status
    try:set_status(db,task,status);action="task.completed" if status==TaskStatus.DONE.value else "task.reopened" if previous==TaskStatus.DONE.value else "task.started" if status==TaskStatus.IN_PROGRESS.value else "task.status_changed";audit_task(db,action,user,task,previous_status=previous);db.commit()
    except TaskValidationError as exc:raise HTTPException(400,str(exc)) from exc
    return RedirectResponse("/tasks",303)

@router.post("/tasks/{task_id}/delete")
def task_delete(request:Request,task_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);task=get_task(db,user.family_id,task_id)
    if not task or not can_delete_task(user,task):raise HTTPException(404,"Aufgabe nicht gefunden")
    audit_task(db,"task.deleted",user,task);db.flush();delete_task(db,task);return RedirectResponse("/tasks",303)
