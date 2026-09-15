from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.content_access import can_access_list, can_access_note
from familienportal.content_audit import audit_list, audit_list_item, audit_note
from familienportal.content_share_models import ContentShare
from familienportal.content_sharing import add_share, remove_share, shares_for_list, shares_for_note
from familienportal.database import get_db
from familienportal.list_models import FamilyList, FamilyListItem, ListKind
from familienportal.list_permissions import can_archive_list, can_create_list, can_delete_list, can_edit_list
from familienportal.models import Household, User, UserStatus
from familienportal.note_models import FamilyNote
from familienportal.note_permissions import can_archive_note, can_create_note, can_delete_note, can_edit_note, can_share_note
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _user(request: Request, db: Session):
    user = _user_from_session(request, db)
    if not user: raise HTTPException(status_code=401)
    return user


def _commit(db: Session) -> None:
    try: db.commit()
    except Exception:
        db.rollback(); raise


def _share_targets(db: Session, user: User):
    users = list(db.scalars(select(User).where(User.family_id == user.family_id, User.status == UserStatus.ACTIVE.value, User.id != user.id).order_by(User.display_name)))
    households = list(db.scalars(select(Household).where(Household.family_id == user.family_id).order_by(Household.name)))
    return users, households


def _share_labels(db: Session, shares: list[ContentShare]) -> list[dict[str, object]]:
    result=[]
    for share in shares:
        if share.user_id:
            target=db.get(User, share.user_id); label=target.display_name if target else "Unbekanntes Mitglied"
            result.append({"id":share.id,"kind":"user","label":label})
        elif share.household_id:
            target=db.get(Household, share.household_id); label=target.name if target else "Unbekannter Haushalt"
            result.append({"id":share.id,"kind":"household","label":label})
    return result


def _can_share_list(user: User, item: FamilyList) -> bool:
    return user.family_id == item.family_id and (user.is_superadmin or has_permission(user,"lists.manage") or (item.owner_user_id == user.id and has_permission(user,"lists.edit")))


@router.get("/notes", response_class=HTMLResponse)
def notes_page(request: Request, archive: bool=False, db: Session=Depends(get_db)):
    user=_user(request,db); filt=FamilyNote.archived_at.is_not(None) if archive else FamilyNote.archived_at.is_(None)
    notes=list(db.scalars(select(FamilyNote).where(FamilyNote.family_id==user.family_id,filt).order_by(FamilyNote.updated_at.desc())))
    visible=[n for n in notes if can_access_note(db,user,n,audit_admin=True)]
    permissions={str(n.id):{"edit":can_edit_note(user,n),"archive":can_archive_note(user,n),"delete":can_delete_note(user,n),"share":can_share_note(user,n)} for n in visible}
    share_map={str(n.id):_share_labels(db,shares_for_note(db,n)) for n in visible if permissions[str(n.id)]["share"]}
    users,households=_share_targets(db,user); _commit(db)
    return templates.TemplateResponse(request,"notes.html",{"user":user,"notes":visible,"archive":archive,"permissions":permissions,"shares":share_map,"share_users":users,"share_households":households})


@router.post("/notes")
def create_note(request:Request,title:str=Form(...),content:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db)
    if not can_create_note(user): raise HTTPException(status_code=403)
    note=FamilyNote(family_id=user.family_id,owner_user_id=user.id,title=title.strip(),content=content,is_private=is_private);db.add(note);db.flush();audit_note(db,"note.created",user,note);_commit(db);return RedirectResponse("/notes",303)


@router.post("/notes/{note_id}/edit")
def edit_note(request:Request,note_id:UUID,title:str=Form(...),content:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or not can_edit_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    note.title=title.strip();note.content=content;note.is_private=is_private;audit_note(db,"note.updated",user,note);_commit(db);return RedirectResponse("/notes",303)


@router.post("/notes/{note_id}/share")
def share_note(request:Request,note_id:UUID,target_type:str=Form(...),target_id:UUID=Form(...),db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or not can_share_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    target=db.get(User,target_id) if target_type=="user" else db.get(Household,target_id) if target_type=="household" else None
    if not target or target.family_id!=user.family_id:raise HTTPException(status_code=400,detail="Ungültiges Freigabeziel")
    add_share(db,user,note=note,**({"user":target} if target_type=="user" else {"household":target}));audit_note(db,"note.shared",user,note,target_type=target_type,target_id=str(target_id));_commit(db);return RedirectResponse("/notes",303)


@router.post("/notes/{note_id}/shares/{share_id}/delete")
def unshare_note(request:Request,note_id:UUID,share_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or not can_share_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    try:remove_share(db,user,share_id,note=note)
    except ValueError:raise HTTPException(status_code=404)
    audit_note(db,"note.unshared",user,note,share_id=str(share_id));_commit(db);return RedirectResponse("/notes",303)


@router.post("/notes/{note_id}/archive")
def archive_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or not can_archive_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    note.archived_at=datetime.now(timezone.utc);audit_note(db,"note.archived",user,note);_commit(db);return RedirectResponse("/notes",303)


@router.post("/notes/{note_id}/restore")
def restore_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or note.archived_at is None or not can_archive_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    note.archived_at=None;audit_note(db,"note.restored",user,note);_commit(db);return RedirectResponse("/notes?archive=true",303)


@router.post("/notes/{note_id}/delete")
def delete_note(request:Request,note_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);note=db.get(FamilyNote,note_id)
    if not note or not can_delete_note(user,note):raise HTTPException(status_code=404 if not note else 403)
    audit_note(db,"note.deleted",user,note);db.delete(note);_commit(db);return RedirectResponse("/notes?archive=true",303)


@router.get("/lists",response_class=HTMLResponse)
def lists_page(request:Request,archive:bool=False,db:Session=Depends(get_db)):
    user=_user(request,db);filt=FamilyList.archived_at.is_not(None) if archive else FamilyList.archived_at.is_(None)
    lists=list(db.scalars(select(FamilyList).where(FamilyList.family_id==user.family_id,filt).order_by(FamilyList.updated_at.desc())));visible=[x for x in lists if can_access_list(db,user,x,audit_admin=True)]
    items=list(db.scalars(select(FamilyListItem).where(FamilyListItem.list_id.in_([x.id for x in visible])).order_by(FamilyListItem.position,FamilyListItem.created_at))) if visible else []
    grouped={str(x.id):[] for x in visible}
    for item in items:grouped[str(item.list_id)].append(item)
    permissions={str(x.id):{"edit":can_edit_list(user,x),"archive":can_archive_list(user,x),"delete":can_delete_list(user,x),"share":_can_share_list(user,x)} for x in visible}
    share_map={str(x.id):_share_labels(db,shares_for_list(db,x)) for x in visible if permissions[str(x.id)]["share"]};users,households=_share_targets(db,user);_commit(db)
    return templates.TemplateResponse(request,"lists.html",{"user":user,"lists":visible,"items":grouped,"kinds":list(ListKind),"archive":archive,"permissions":permissions,"shares":share_map,"share_users":users,"share_households":households})


@router.post("/lists")
def create_list(request:Request,title:str=Form(...),kind:str=Form(ListKind.GENERAL.value),description:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db)
    if not can_create_list(user):raise HTTPException(status_code=403)
    if kind not in {x.value for x in ListKind}:raise HTTPException(status_code=400)
    x=FamilyList(family_id=user.family_id,owner_user_id=user.id,title=title.strip(),description=description,kind=kind,is_private=is_private);db.add(x);db.flush();audit_list(db,"list.created",user,x);_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/share")
def share_list(request:Request,list_id:UUID,target_type:str=Form(...),target_id:UUID=Form(...),db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or not _can_share_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    target=db.get(User,target_id) if target_type=="user" else db.get(Household,target_id) if target_type=="household" else None
    if not target or target.family_id!=user.family_id:raise HTTPException(status_code=400,detail="Ungültiges Freigabeziel")
    add_share(db,user,family_list=x,**({"user":target} if target_type=="user" else {"household":target}));audit_list(db,"list.shared",user,x,target_type=target_type,target_id=str(target_id));_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/shares/{share_id}/delete")
def unshare_list(request:Request,list_id:UUID,share_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or not _can_share_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    try:remove_share(db,user,share_id,family_list=x)
    except ValueError:raise HTTPException(status_code=404)
    audit_list(db,"list.unshared",user,x,share_id=str(share_id));_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/edit")
def edit_list(request:Request,list_id:UUID,title:str=Form(...),kind:str=Form(ListKind.GENERAL.value),description:str=Form(""),is_private:bool=Form(False),db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or not can_edit_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    if kind not in {k.value for k in ListKind}:raise HTTPException(status_code=400)
    x.title=title.strip();x.kind=kind;x.description=description;x.is_private=is_private;audit_list(db,"list.updated",user,x);_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/archive")
def archive_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or not can_archive_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    x.archived_at=datetime.now(timezone.utc);audit_list(db,"list.archived",user,x);_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/restore")
def restore_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or x.archived_at is None or not can_archive_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    x.archived_at=None;audit_list(db,"list.restored",user,x);_commit(db);return RedirectResponse("/lists?archive=true",303)


@router.post("/lists/{list_id}/delete")
def delete_list(request:Request,list_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or not can_delete_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    audit_list(db,"list.deleted",user,x);db.delete(x);_commit(db);return RedirectResponse("/lists?archive=true",303)


@router.post("/lists/{list_id}/items")
def add_list_item(request:Request,list_id:UUID,title:str=Form(...),quantity:float|None=Form(None),unit:str=Form(""),category:str=Form(""),db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id)
    if not x or x.archived_at is not None or not can_edit_list(user,x):raise HTTPException(status_code=404 if not x else 403)
    item=FamilyListItem(list_id=x.id,title=title.strip(),quantity=quantity,unit=unit or None,category=category or None);db.add(item);db.flush();audit_list_item(db,"list_item.created",user,item);_commit(db);return RedirectResponse("/lists",303)


@router.post("/lists/{list_id}/items/{item_id}/toggle")
def toggle_list_item(request:Request,list_id:UUID,item_id:UUID,db:Session=Depends(get_db)):
    user=_user(request,db);x=db.get(FamilyList,list_id);item=db.get(FamilyListItem,item_id)
    if not x or x.archived_at is not None or not item or item.list_id!=x.id or not can_edit_list(user,x):raise HTTPException(status_code=404)
    item.is_done=not item.is_done;audit_list_item(db,"list_item.toggled",user,item);_commit(db);return RedirectResponse("/lists",303)
