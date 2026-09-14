from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.models import Family, Household, User
from familienportal.nextcloud import NextcloudError
from familienportal.nextcloud_models import NextcloudFamilyFolder, NextcloudGroupMapping, NextcloudUserMapping
from familienportal.nextcloud_web import _client, _state
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/platform/nextcloud/management", response_class=HTMLResponse)
def management_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    users = db.scalars(select(User).where(User.family_id == admin.family_id).order_by(User.display_name)).all()
    households = db.scalars(select(Household).where(Household.family_id == admin.family_id).order_by(Household.name)).all()
    user_mappings = db.scalars(select(NextcloudUserMapping).where(NextcloudUserMapping.family_id == admin.family_id)).all()
    group_mappings = db.scalars(select(NextcloudGroupMapping).where(NextcloudGroupMapping.family_id == admin.family_id)).all()
    folders = db.scalars(select(NextcloudFamilyFolder).where(NextcloudFamilyFolder.family_id == admin.family_id).order_by(NextcloudFamilyFolder.name)).all()
    remote_users: list[str] = []
    remote_groups: list[str] = []
    diagnostics: dict[str, str] = {}
    error: str | None = None
    if state and state.enabled:
        try:
            client = _client(state)
            remote_users = client.list_users()
            remote_groups = client.list_groups()
            diagnostics = client.diagnostics()
        except (HTTPException, NextcloudError) as exc:
            error = str(exc.detail) if isinstance(exc, HTTPException) else str(exc)
    return templates.TemplateResponse(request=request, name="nextcloud_management.html", context={
        "user": admin, "is_admin": True, "state": state, "users": users, "households": households,
        "user_mappings": user_mappings, "group_mappings": group_mappings, "folders": folders,
        "remote_users": remote_users, "remote_groups": remote_groups, "diagnostics": diagnostics, "error": error,
        "family_id": admin.family_id,
    })


@router.post("/platform/nextcloud/management/users")
def map_user(request: Request, user_id: UUID = Form(...), nextcloud_user_id: str = Form(...), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    user = db.get(User, user_id)
    remote_id = nextcloud_user_id.strip()
    if not user or user.family_id != admin.family_id or not remote_id:
        raise HTTPException(status_code=400, detail="Ungültige Benutzerzuordnung")
    conflict = db.scalar(select(NextcloudUserMapping).where(NextcloudUserMapping.family_id == admin.family_id, NextcloudUserMapping.nextcloud_user_id == remote_id, NextcloudUserMapping.user_id != user_id))
    if conflict:
        raise HTTPException(status_code=409, detail="Nextcloud-Benutzer bereits zugeordnet")
    mapping = db.scalar(select(NextcloudUserMapping).where(NextcloudUserMapping.family_id == admin.family_id, NextcloudUserMapping.user_id == user_id))
    if mapping:
        mapping.nextcloud_user_id = remote_id
    else:
        db.add(NextcloudUserMapping(family_id=admin.family_id, user_id=user_id, nextcloud_user_id=remote_id))
    audit(db, "nextcloud.user_mapping.updated", actor=admin, target_type="user", target_id=str(user_id), details=remote_id)
    db.commit()
    return RedirectResponse("/platform/nextcloud/management#users", status_code=303)


@router.post("/platform/nextcloud/management/groups")
def map_group(request: Request, target_type: str = Form(...), target_id: UUID = Form(...), nextcloud_group_id: str = Form(...), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    remote_group = nextcloud_group_id.strip()
    if target_type == "family":
        target = db.get(Family, target_id)
        valid = bool(target and target.id == admin.family_id)
    elif target_type == "household":
        target = db.get(Household, target_id)
        valid = bool(target and target.family_id == admin.family_id)
    else:
        valid = False
    if not valid or not remote_group:
        raise HTTPException(status_code=400, detail="Ungültige Gruppenzuordnung")
    mapping = db.scalar(select(NextcloudGroupMapping).where(NextcloudGroupMapping.family_id == admin.family_id, NextcloudGroupMapping.target_type == target_type, NextcloudGroupMapping.target_id == target_id))
    if mapping:
        mapping.nextcloud_group_id = remote_group
    else:
        db.add(NextcloudGroupMapping(family_id=admin.family_id, target_type=target_type, target_id=target_id, nextcloud_group_id=remote_group))
    audit(db, "nextcloud.group_mapping.updated", actor=admin, target_type=target_type, target_id=str(target_id), details=remote_group)
    db.commit()
    return RedirectResponse("/platform/nextcloud/management#groups", status_code=303)


@router.post("/platform/nextcloud/management/folders")
def create_folder(request: Request, name: str = Form(...), path: str = Form(...), household_id: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state:
        raise HTTPException(status_code=409, detail="Nextcloud ist nicht konfiguriert")
    clean_name = name.strip()
    clean_path = path.strip().strip("/")
    household_uuid = UUID(household_id) if household_id else None
    if household_uuid:
        household = db.get(Household, household_uuid)
        if not household or household.family_id != admin.family_id:
            raise HTTPException(status_code=400, detail="Ungültiger Haushalt")
    if not clean_name or not clean_path:
        raise HTTPException(status_code=400, detail="Name und Pfad sind erforderlich")
    if db.scalar(select(NextcloudFamilyFolder).where(NextcloudFamilyFolder.family_id == admin.family_id, NextcloudFamilyFolder.path == clean_path)):
        raise HTTPException(status_code=409, detail="Familienordner bereits registriert")
    try:
        _client(state).create_folder(clean_path)
    except NextcloudError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    db.add(NextcloudFamilyFolder(family_id=admin.family_id, household_id=household_uuid, name=clean_name, path=clean_path))
    audit(db, "nextcloud.family_folder.created", actor=admin, target_type="nextcloud_folder", target_id=clean_path)
    db.commit()
    return RedirectResponse("/platform/nextcloud/management#folders", status_code=303)
