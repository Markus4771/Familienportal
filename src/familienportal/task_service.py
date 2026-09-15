from __future__ import annotations
from datetime import datetime,timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from familienportal.models import Household,User
from familienportal.task_calendar import sync_task_event
from familienportal.task_models import FamilyTask,TaskPriority,TaskStatus
from familienportal.task_recurrence import next_due_at
VALID_STATUSES={i.value for i in TaskStatus};VALID_PRIORITIES={i.value for i in TaskPriority};VALID_RECURRENCES={None,"daily","weekly","monthly","yearly"}
class TaskValidationError(ValueError):pass
def _clean_title(v):
 v=v.strip()
 if not v:raise TaskValidationError("Titel darf nicht leer sein.")
 if len(v)>240:raise TaskValidationError("Titel darf maximal 240 Zeichen enthalten.")
 return v
def _clean_description(v):return (v.strip() or None) if v is not None else None
def _family_user(db,fid,uid):
 if uid is not None and db.scalar(select(User.id).where(User.id==uid,User.family_id==fid)) is None:raise TaskValidationError("Zugewiesener Benutzer gehört nicht zu dieser Familie.")
 return uid
def _family_household(db,fid,hid):
 if hid is not None and db.scalar(select(Household.id).where(Household.id==hid,Household.family_id==fid)) is None:raise TaskValidationError("Haushalt gehört nicht zu dieser Familie.")
 return hid
def _finish(db,task,commit):
 if commit:
  db.commit();db.refresh(task)
 else:db.flush()
 return task
def get_task(db,family_id,task_id):return db.scalar(select(FamilyTask).where(FamilyTask.id==task_id,FamilyTask.family_id==family_id))
def list_tasks(db,family_id,*,status=None,assignee_user_id=None,archived=False):
 q=select(FamilyTask).where(FamilyTask.family_id==family_id,FamilyTask.archived_at.is_not(None) if archived else FamilyTask.archived_at.is_(None))
 if status:
  if status not in VALID_STATUSES:raise TaskValidationError("Ungültiger Aufgabenstatus.")
  q=q.where(FamilyTask.status==status)
 if assignee_user_id:q=q.where(FamilyTask.assignee_user_id==assignee_user_id)
 return list(db.scalars(q.order_by(FamilyTask.due_at.asc().nullslast(),FamilyTask.created_at.desc())).all())
def create_task(db:Session,*,family_id:UUID,creator_user_id:UUID,title:str,description=None,household_id=None,assignee_user_id=None,priority="normal",due_at=None,recurrence=None,recurrence_interval=1,is_private=False,commit=True):
 if priority not in VALID_PRIORITIES:raise TaskValidationError("Ungültige Priorität.")
 if recurrence not in VALID_RECURRENCES:raise TaskValidationError("Ungültige Wiederholung.")
 if not 1<=recurrence_interval<=365:raise TaskValidationError("Wiederholungsintervall muss zwischen 1 und 365 liegen.")
 t=FamilyTask(family_id=family_id,creator_user_id=_family_user(db,family_id,creator_user_id),household_id=_family_household(db,family_id,household_id),assignee_user_id=_family_user(db,family_id,assignee_user_id),title=_clean_title(title),description=_clean_description(description),priority=priority,due_at=due_at,recurrence=recurrence,recurrence_interval=recurrence_interval,is_private=is_private);db.add(t);db.flush();sync_task_event(db,t);return _finish(db,t,commit)
def update_task(db,task,*,title,description,household_id,assignee_user_id,priority,due_at,recurrence,recurrence_interval,is_private,commit=True):
 if priority not in VALID_PRIORITIES or recurrence not in VALID_RECURRENCES or not 1<=recurrence_interval<=365:raise TaskValidationError("Ungültige Aufgabendaten.")
 task.title=_clean_title(title);task.description=_clean_description(description);task.household_id=_family_household(db,task.family_id,household_id);task.assignee_user_id=_family_user(db,task.family_id,assignee_user_id);task.priority=priority;task.due_at=due_at;task.recurrence=recurrence;task.recurrence_interval=recurrence_interval;task.is_private=is_private;sync_task_event(db,task);return _finish(db,task,commit)
def _next_recurring_task(t,completed):
 due=next_due_at(t,completed)
 return None if due is None else FamilyTask(family_id=t.family_id,household_id=t.household_id,creator_user_id=t.creator_user_id,assignee_user_id=t.assignee_user_id,title=t.title,description=t.description,status="open",priority=t.priority,due_at=due,recurrence=t.recurrence,recurrence_interval=t.recurrence_interval,is_private=t.is_private)
def set_status(db,task,status,*,commit=True):
 if status not in VALID_STATUSES:raise TaskValidationError("Ungültiger Aufgabenstatus.")
 was=task.status=="done";task.status=status;task.completed_at=datetime.now(timezone.utc) if status=="done" else None;sync_task_event(db,task)
 if status=="done" and not was and task.recurrence:
  n=_next_recurring_task(task,task.completed_at)
  if n:db.add(n);db.flush();sync_task_event(db,n)
 return _finish(db,task,commit)
def archive_task(db,task,*,commit=True):
 task.archived_at=datetime.now(timezone.utc);sync_task_event(db,task);return _finish(db,task,commit)
def restore_task(db,task,*,commit=True):
 task.archived_at=None;sync_task_event(db,task);return _finish(db,task,commit)
def delete_task(db,task,*,commit=True):
 task.status="cancelled";sync_task_event(db,task);db.delete(task)
 if commit:db.commit()
 else:db.flush()
