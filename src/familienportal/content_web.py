from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter,Depends,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from familienportal.content_access import can_access_list,can_access_note
from familienportal.content_actions import create_event_from_content,create_task_from_content
from familienportal.content_audit import audit_list,audit_list_item,audit_note
from familienportal.content_link_service import links_for_list,links_for_note
from familienportal.content_share_models import ContentShare
from familienportal.content_sharing import add_share,remove_share,shares_for_list,shares_for_note
from familienportal.database import get_db
from familienportal.list_item_service import add_item,move_item,update_item
from familienportal.list_models import FamilyList,FamilyListItem,ListKind
from familienportal.list_permissions import can_archive_list,can_create_list,can_delete_list,can_edit_list
from familienportal.models import Household,User,UserStatus
from familienportal.note_models import FamilyNote
from familienportal.note_permissions import can_archive_note,can_create_note,can_delete_note,can_edit_note,can_share_note
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session
router=APIRouter(include_in_schema=False);templates=Jinja2Templates(directory="src/familienportal/templates")
def _user(r,db):
 u=_user_from_session(r,db)
 if not u:raise HTTPException(401)
 return u
def _commit(db):
 try:db.commit()
 except Exception:db.rollback();raise
def _dt(v):return datetime.fromisoformat(v) if v else None
def _targets(db,u):return list(db.scalars(select(User).where(User.family_id==u.family_id,User.status==UserStatus.ACTIVE.value).order_by(User.display_name))),list(db.scalars(select(Household).where(Household.family_id==u.family_id).order_by(Household.name)))
def _labels(db,ss):
 out=[]
 for s in ss:
  x=db.get(User,s.user_id) if s.user_id else db.get(Household,s.household_id);out.append({"id":s.id,"kind":"user" if s.user_id else "household","label":x.display_name if s.user_id and x else x.name if x else "Unbekannt"})
 return out
def _share_list(u,x):return u.family_id==x.family_id and (u.is_superadmin or has_permission(u,"lists.manage") or (x.owner_user_id==u.id and has_permission(u,"lists.edit")))
def _links(db,objects,is_note):return {str(x.id):links_for_note(db,x) if is_note else links_for_list(db,x) for x in objects}
@router.get("/notes",response_class=HTMLResponse)
def notes_page(request:Request,archive:bool=False,db:Session=Depends(get_db)):
 u=_user(request,db);f=FamilyNote.archived_at.is_not(None) if archive else FamilyNote.archived_at.is_(None);all=list(db.scalars(select(FamilyNote).where(FamilyNote.family_id==u.family_id,f).order_by(FamilyNote.updated_at.desc())));visible=[x for x in all if can_access_note(db,u,x,audit_admin=True)];p={str(x.id):{"edit":can_edit_note(u,x),"archive":can_archive_note(u,x),"delete":can_delete_note(u,x),"share":can_share_note(u,x)} for x in visible};users,households=_targets(db,u);shares={str(x.id):_labels(db,shares_for_note(db,x)) for x in visible if p[str(x.id)]["share"]};links=_links(db,visible,True);_commit(db);return templates.TemplateResponse(request,"notes.html",{"user":u,"notes":visible,"archive":archive,"permissions":p,"shares":shares,"share_users":users,"share_households":households,"links":links})
@router.post("/notes")
def create_note(request:Request,title:str=Form(...),content:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
 u=_user(request,db)
 if not can_create_note(u):raise HTTPException(403)
 x=FamilyNote(family_id=u.family_id,owner_user_id=u.id,title=title.strip(),content=content,is_private=is_private);db.add(x);db.flush();audit_note(db,"note.created",u,x);_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/edit")
def edit_note(request:Request,note_id:UUID,title:str=Form(...),content:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or not can_edit_note(u,x):raise HTTPException(404 if not x else 403)
 x.title=title.strip();x.content=content;x.is_private=is_private;audit_note(db,"note.updated",u,x);_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/task")
def note_task(request:Request,note_id:UUID,due_at:str=Form(""),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or x.archived_at or not can_access_note(db,u,x):raise HTTPException(404)
 t=create_task_from_content(db,u,note=x,due_at=_dt(due_at));audit_note(db,"note.task_created",u,x,task_id=str(t.id));_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/event")
def note_event(request:Request,note_id:UUID,starts_at:str=Form(...),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or x.archived_at or not can_access_note(db,u,x):raise HTTPException(404)
 try:e=create_event_from_content(db,u,note=x,starts_at=_dt(starts_at));audit_note(db,"note.event_created",u,x,event_id=str(e.id));_commit(db)
 except ValueError as exc:db.rollback();raise HTTPException(400,str(exc))
 return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/share")
def share_note(request:Request,note_id:UUID,target_type:str=Form(...),target_id:UUID=Form(...),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or not can_share_note(u,x):raise HTTPException(404 if not x else 403)
 target=db.get(User,target_id) if target_type=="user" else db.get(Household,target_id) if target_type=="household" else None
 if not target or target.family_id!=u.family_id:raise HTTPException(400)
 add_share(db,u,note=x,**({"user":target} if target_type=="user" else {"household":target}));audit_note(db,"note.shared",u,x,target_type=target_type,target_id=str(target_id));_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/shares/{share_id}/delete")
def unshare_note(request:Request,note_id:UUID,share_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or not can_share_note(u,x):raise HTTPException(404 if not x else 403)
 try:remove_share(db,u,share_id,note=x)
 except ValueError:raise HTTPException(404)
 audit_note(db,"note.unshared",u,x,share_id=str(share_id));_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/archive")
def archive_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or not can_archive_note(u,x):raise HTTPException(404 if not x else 403)
 x.archived_at=datetime.now(timezone.utc);audit_note(db,"note.archived",u,x);_commit(db);return RedirectResponse("/notes",303)
@router.post("/notes/{note_id}/restore")
def restore_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or x.archived_at is None or not can_archive_note(u,x):raise HTTPException(404 if not x else 403)
 x.archived_at=None;audit_note(db,"note.restored",u,x);_commit(db);return RedirectResponse("/notes?archive=true",303)
@router.post("/notes/{note_id}/delete")
def delete_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyNote,note_id)
 if not x or not can_delete_note(u,x):raise HTTPException(404 if not x else 403)
 audit_note(db,"note.deleted",u,x);db.delete(x);_commit(db);return RedirectResponse("/notes?archive=true",303)
@router.get("/lists",response_class=HTMLResponse)
def lists_page(request:Request,archive:bool=False,db:Session=Depends(get_db)):
 u=_user(request,db);f=FamilyList.archived_at.is_not(None) if archive else FamilyList.archived_at.is_(None);all=list(db.scalars(select(FamilyList).where(FamilyList.family_id==u.family_id,f).order_by(FamilyList.updated_at.desc())));visible=[x for x in all if can_access_list(db,u,x,audit_admin=True)];raw=list(db.scalars(select(FamilyListItem).where(FamilyListItem.list_id.in_([x.id for x in visible])).order_by(FamilyListItem.is_done,FamilyListItem.position,FamilyListItem.due_at.asc().nullslast(),FamilyListItem.created_at))) if visible else [];items={str(x.id):[] for x in visible}
 for i in raw:items[str(i.list_id)].append(i)
 p={str(x.id):{"edit":can_edit_list(u,x),"archive":can_archive_list(u,x),"delete":can_delete_list(u,x),"share":_share_list(u,x)} for x in visible};users,households=_targets(db,u);shares={str(x.id):_labels(db,shares_for_list(db,x)) for x in visible if p[str(x.id)]["share"]};links=_links(db,visible,False);_commit(db);return templates.TemplateResponse(request,"lists.html",{"user":u,"lists":visible,"items":items,"archive":archive,"permissions":p,"shares":shares,"share_users":users,"share_households":households,"family_users":users,"links":links})
@router.post("/lists")
def create_list(request:Request,title:str=Form(...),kind:str=Form("general"),description:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
 u=_user(request,db)
 if not can_create_list(u):raise HTTPException(403)
 if kind not in {x.value for x in ListKind}:raise HTTPException(400)
 x=FamilyList(family_id=u.family_id,owner_user_id=u.id,title=title.strip(),description=description,kind=kind,is_private=is_private);db.add(x);db.flush();audit_list(db,"list.created",u,x);_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/task")
def list_task(request:Request,list_id:UUID,due_at:str=Form(""),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or x.archived_at or not can_access_list(db,u,x):raise HTTPException(404)
 t=create_task_from_content(db,u,family_list=x,due_at=_dt(due_at));audit_list(db,"list.task_created",u,x,task_id=str(t.id));_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/event")
def list_event(request:Request,list_id:UUID,starts_at:str=Form(...),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or x.archived_at or not can_access_list(db,u,x):raise HTTPException(404)
 try:e=create_event_from_content(db,u,family_list=x,starts_at=_dt(starts_at));audit_list(db,"list.event_created",u,x,event_id=str(e.id));_commit(db)
 except ValueError as exc:db.rollback();raise HTTPException(400,str(exc))
 return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/share")
def share_list(request:Request,list_id:UUID,target_type:str=Form(...),target_id:UUID=Form(...),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or not _share_list(u,x):raise HTTPException(404 if not x else 403)
 target=db.get(User,target_id) if target_type=="user" else db.get(Household,target_id) if target_type=="household" else None
 if not target or target.family_id!=u.family_id:raise HTTPException(400)
 add_share(db,u,family_list=x,**({"user":target} if target_type=="user" else {"household":target}));audit_list(db,"list.shared",u,x,target_type=target_type,target_id=str(target_id));_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/shares/{share_id}/delete")
def unshare_list(request:Request,list_id:UUID,share_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or not _share_list(u,x):raise HTTPException(404 if not x else 403)
 try:remove_share(db,u,share_id,family_list=x)
 except ValueError:raise HTTPException(404)
 audit_list(db,"list.unshared",u,x,share_id=str(share_id));_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/edit")
def edit_list(request:Request,list_id:UUID,title:str=Form(...),kind:str=Form("general"),description:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or not can_edit_list(u,x):raise HTTPException(404 if not x else 403)
 x.title=title.strip();x.kind=kind;x.description=description;x.is_private=is_private;audit_list(db,"list.updated",u,x);_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/archive")
def archive_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or not can_archive_list(u,x):raise HTTPException(404 if not x else 403)
 x.archived_at=datetime.now(timezone.utc);audit_list(db,"list.archived",u,x);_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/restore")
def restore_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or x.archived_at is None or not can_archive_list(u,x):raise HTTPException(404 if not x else 403)
 x.archived_at=None;audit_list(db,"list.restored",u,x);_commit(db);return RedirectResponse("/lists?archive=true",303)
@router.post("/lists/{list_id}/delete")
def delete_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or not can_delete_list(u,x):raise HTTPException(404 if not x else 403)
 audit_list(db,"list.deleted",u,x);db.delete(x);_commit(db);return RedirectResponse("/lists?archive=true",303)
@router.post("/lists/{list_id}/items")
def add_list_item(request:Request,list_id:UUID,title:str=Form(...),quantity:Decimal|None=Form(None),unit:str=Form(""),category:str=Form(""),assignee_user_id:UUID|None=Form(None),due_at:str=Form(""),note:str=Form(""),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id)
 if not x or x.archived_at or not can_edit_list(u,x):raise HTTPException(404 if not x else 403)
 try:i=add_item(db,x,title=title,quantity=quantity,unit=unit,category=category,assignee_user_id=assignee_user_id,due_at=_dt(due_at),note=note);db.flush();audit_list_item(db,"list_item.created",u,i);_commit(db)
 except ValueError as exc:db.rollback();raise HTTPException(400,str(exc))
 return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/items/{item_id}/edit")
def edit_item(request:Request,list_id:UUID,item_id:UUID,title:str=Form(...),quantity:Decimal|None=Form(None),unit:str=Form(""),category:str=Form(""),assignee_user_id:UUID|None=Form(None),due_at:str=Form(""),note:str=Form(""),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id);i=db.get(FamilyListItem,item_id)
 if not x or not i or x.archived_at or not can_edit_list(u,x):raise HTTPException(404)
 try:update_item(db,x,i,title=title,quantity=quantity,unit=unit,category=category,assignee_user_id=assignee_user_id,due_at=_dt(due_at),note=note);audit_list_item(db,"list_item.updated",u,i);_commit(db)
 except ValueError as exc:db.rollback();raise HTTPException(400,str(exc))
 return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/items/{item_id}/move")
def move_list_item(request:Request,list_id:UUID,item_id:UUID,position:int=Form(...),db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id);i=db.get(FamilyListItem,item_id)
 if not x or not i or i.list_id!=x.id or not can_edit_list(u,x):raise HTTPException(404)
 move_item(i,position=position);audit_list_item(db,"list_item.moved",u,i,position=i.position);_commit(db);return RedirectResponse("/lists",303)
@router.post("/lists/{list_id}/items/{item_id}/toggle")
def toggle_list_item(request:Request,list_id:UUID,item_id:UUID,db:Session=Depends(get_db)):
 u=_user(request,db);x=db.get(FamilyList,list_id);i=db.get(FamilyListItem,item_id)
 if not x or x.archived_at or not i or i.list_id!=x.id or not can_edit_list(u,x):raise HTTPException(404)
 i.is_done=not i.is_done;audit_list_item(db,"list_item.toggled",u,i);_commit(db);return RedirectResponse("/lists",303)
