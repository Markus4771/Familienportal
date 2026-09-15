from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.content_audit import audit_list, audit_list_item, audit_note
from familienportal.database import get_db
from familienportal.list_models import FamilyList, FamilyListItem, ListKind
from familienportal.list_permissions import can_create_list, can_edit_list, can_read_list
from familienportal.note_models import FamilyNote
from familienportal.note_permissions import can_archive_note, can_create_note, can_edit_note, can_read_note
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _user(request: Request, db: Session):
    user = _user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=401)
    return user


@router.get("/notes", response_class=HTMLResponse)
def notes_page(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    notes = list(db.scalars(select(FamilyNote).where(FamilyNote.family_id == user.family_id, FamilyNote.archived_at.is_(None)).order_by(FamilyNote.updated_at.desc())))
    return templates.TemplateResponse(request, "notes.html", {"user": user, "notes": [n for n in notes if can_read_note(user, n)]})


@router.post("/notes")
def create_note(request: Request, title: str = Form(...), content: str = Form(""), is_private: bool = Form(False), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not can_create_note(user):
        raise HTTPException(status_code=403)
    note = FamilyNote(family_id=user.family_id, owner_user_id=user.id, title=title.strip(), content=content, is_private=is_private)
    db.add(note); db.flush(); audit_note(db, "note.created", user, note); db.commit()
    return RedirectResponse("/notes", status_code=303)


@router.post("/notes/{note_id}/edit")
def edit_note(request: Request, note_id: UUID, title: str = Form(...), content: str = Form(""), is_private: bool = Form(False), db: Session = Depends(get_db)):
    user = _user(request, db); note = db.get(FamilyNote, note_id)
    if not note or not can_edit_note(user, note): raise HTTPException(status_code=404 if not note else 403)
    note.title = title.strip(); note.content = content; note.is_private = is_private
    audit_note(db, "note.updated", user, note); db.commit(); return RedirectResponse("/notes", status_code=303)


@router.post("/notes/{note_id}/archive")
def archive_note(request: Request, note_id: UUID, db: Session = Depends(get_db)):
    user = _user(request, db); note = db.get(FamilyNote, note_id)
    if not note or not can_archive_note(user, note): raise HTTPException(status_code=404 if not note else 403)
    note.archived_at = datetime.now(timezone.utc); audit_note(db, "note.archived", user, note); db.commit()
    return RedirectResponse("/notes", status_code=303)


@router.get("/lists", response_class=HTMLResponse)
def lists_page(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    lists = list(db.scalars(select(FamilyList).where(FamilyList.family_id == user.family_id, FamilyList.archived_at.is_(None)).order_by(FamilyList.updated_at.desc())))
    visible = [item for item in lists if can_read_list(user, item)]
    items = list(db.scalars(select(FamilyListItem).where(FamilyListItem.list_id.in_([x.id for x in visible])).order_by(FamilyListItem.position, FamilyListItem.created_at))) if visible else []
    grouped = {str(x.id): [] for x in visible}
    for item in items: grouped[str(item.list_id)].append(item)
    return templates.TemplateResponse(request, "lists.html", {"user": user, "lists": visible, "items": grouped, "kinds": list(ListKind)})


@router.post("/lists")
def create_list(request: Request, title: str = Form(...), kind: str = Form(ListKind.GENERAL.value), description: str = Form(""), is_private: bool = Form(False), db: Session = Depends(get_db)):
    user = _user(request, db)
    if not can_create_list(user): raise HTTPException(status_code=403)
    if kind not in {x.value for x in ListKind}: raise HTTPException(status_code=400, detail="Ungültiger Listentyp")
    family_list = FamilyList(family_id=user.family_id, owner_user_id=user.id, title=title.strip(), description=description, kind=kind, is_private=is_private)
    db.add(family_list); db.flush(); audit_list(db, "list.created", user, family_list); db.commit()
    return RedirectResponse("/lists", status_code=303)


@router.post("/lists/{list_id}/items")
def add_list_item(request: Request, list_id: UUID, title: str = Form(...), quantity: float | None = Form(None), unit: str = Form(""), category: str = Form(""), db: Session = Depends(get_db)):
    user = _user(request, db); family_list = db.get(FamilyList, list_id)
    if not family_list or not can_edit_list(user, family_list): raise HTTPException(status_code=404 if not family_list else 403)
    item = FamilyListItem(list_id=family_list.id, title=title.strip(), quantity=quantity, unit=unit or None, category=category or None)
    db.add(item); db.flush(); audit_list_item(db, "list_item.created", user, item); db.commit()
    return RedirectResponse("/lists", status_code=303)


@router.post("/lists/{list_id}/items/{item_id}/toggle")
def toggle_list_item(request: Request, list_id: UUID, item_id: UUID, db: Session = Depends(get_db)):
    user = _user(request, db); family_list = db.get(FamilyList, list_id); item = db.get(FamilyListItem, item_id)
    if not family_list or not item or item.list_id != family_list.id or not can_edit_list(user, family_list): raise HTTPException(status_code=404)
    item.is_done = not item.is_done; audit_list_item(db, "list_item.toggled", user, item); db.commit()
    return RedirectResponse("/lists", status_code=303)
