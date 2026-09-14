from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.extensions import BUILTIN_CONNECTORS, BUILTIN_MODULES
from familienportal.models import Family, Role, User, UserStatus
from familienportal.platform_models import ConnectorState, FamilySetting, ModuleState

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _admin(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    try:
        user = db.get(User, UUID(user_id))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung") from exc
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    if not (user.is_superadmin or any(role.name == "Administrator" for role in user.roles)):
        raise HTTPException(status_code=403, detail="Administratorrecht erforderlich")
    return user


def _module_rows(db: Session, family_id: UUID) -> list[dict[str, object]]:
    states = {item.module_key: item for item in db.scalars(select(ModuleState).where(ModuleState.family_id == family_id)).all()}
    rows = []
    for key, definition in BUILTIN_MODULES.items():
        state = states.get(key)
        rows.append({"key": key, **definition, "enabled": state.enabled if state else bool(definition.get("default"))})
    return rows


def _connector_rows(db: Session, family_id: UUID) -> list[dict[str, object]]:
    states = {item.connector_key: item for item in db.scalars(select(ConnectorState).where(ConnectorState.family_id == family_id)).all()}
    rows = []
    for key, definition in BUILTIN_CONNECTORS.items():
        state = states.get(key)
        rows.append({
            "key": key,
            **definition,
            "enabled": bool(state and state.enabled),
            "base_url": state.base_url if state else "",
            "health_status": state.health_status if state else "not_checked",
            "health_message": state.health_message if state else None,
        })
    return rows


@router.get("/platform", response_class=HTMLResponse)
def platform_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    return templates.TemplateResponse(
        request=request,
        name="platform.html",
        context={"user": admin, "is_admin": True, "modules": _module_rows(db, admin.family_id), "connectors": _connector_rows(db, admin.family_id)},
    )


@router.post("/platform/modules/{module_key}/toggle")
def toggle_module(module_key: str, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    if module_key not in BUILTIN_MODULES:
        raise HTTPException(status_code=404, detail="Modul nicht gefunden")
    state = db.scalar(select(ModuleState).where(ModuleState.family_id == admin.family_id, ModuleState.module_key == module_key))
    if not state:
        state = ModuleState(family_id=admin.family_id, module_key=module_key, enabled=not bool(BUILTIN_MODULES[module_key].get("default")))
        db.add(state)
    else:
        state.enabled = not state.enabled
    audit(db, "module.toggled", actor=admin, target_type="module", target_id=module_key, details=f"enabled={state.enabled}")
    db.commit()
    return RedirectResponse("/platform#modules", status_code=303)


@router.post("/platform/connectors/{connector_key}")
def save_connector(connector_key: str, request: Request, enabled: bool = Form(False), base_url: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    if connector_key not in BUILTIN_CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector nicht gefunden")
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == admin.family_id, ConnectorState.connector_key == connector_key))
    if not state:
        state = ConnectorState(family_id=admin.family_id, connector_key=connector_key)
        db.add(state)
    state.enabled = enabled
    state.base_url = base_url.strip().rstrip("/") or None
    state.health_status = "configured" if enabled and state.base_url else "not_checked"
    state.health_message = None
    audit(db, "connector.updated", actor=admin, target_type="connector", target_id=connector_key)
    db.commit()
    return RedirectResponse("/platform#connectors", status_code=303)


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    family = db.get(Family, admin.family_id)
    stored = {item.setting_key: item.value for item in db.scalars(select(FamilySetting).where(FamilySetting.family_id == admin.family_id)).all()}
    return templates.TemplateResponse(request=request, name="settings.html", context={"user": admin, "is_admin": True, "family": family, "settings": stored})


@router.post("/settings")
def save_settings(request: Request, portal_title: str = Form("Familienportal"), timezone_name: str = Form("Europe/Berlin"), language: str = Form("de"), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    values = {"portal_title": portal_title.strip() or "Familienportal", "timezone": timezone_name.strip() or "Europe/Berlin", "language": language.strip() or "de"}
    for key, value in values.items():
        item = db.scalar(select(FamilySetting).where(FamilySetting.family_id == admin.family_id, FamilySetting.setting_key == key))
        if item:
            item.value = value
        else:
            db.add(FamilySetting(family_id=admin.family_id, setting_key=key, value=value))
    audit(db, "settings.updated", actor=admin, target_type="family", target_id=str(admin.family_id))
    db.commit()
    return RedirectResponse("/settings?saved=1", status_code=303)


@router.get("/admin/roles", response_class=HTMLResponse)
def roles_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    roles = db.scalars(select(Role).where(Role.family_id == admin.family_id).order_by(Role.name)).all()
    return templates.TemplateResponse(request=request, name="roles.html", context={"user": admin, "is_admin": True, "roles": roles})


@router.post("/admin/roles/{role_id}")
def save_role(role_id: UUID, request: Request, permissions: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    role = db.get(Role, role_id)
    if not role or role.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Rolle nicht gefunden")
    role.permissions = ",".join(sorted({item.strip() for item in permissions.split(",") if item.strip()}))
    audit(db, "role.permissions.updated", actor=admin, target_type="role", target_id=str(role.id))
    db.commit()
    return RedirectResponse("/admin/roles?saved=1", status_code=303)
