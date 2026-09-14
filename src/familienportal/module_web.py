from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.extensions import BUILTIN_MODULES
from familienportal.models import User, UserStatus
from familienportal.permissions import has_permission
from familienportal.platform_models import ModuleState
from familienportal.platform_runtime import enabled_modules

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _current_user(request: Request, db: Session) -> User | None:
    value = request.session.get("user_id")
    if not value:
        return None
    try:
        user = db.get(User, UUID(value))
    except ValueError:
        return None
    if not user or user.status != UserStatus.ACTIVE.value:
        return None
    return user


@router.get("/modules/{module_key}", response_class=HTMLResponse)
def module_entry(module_key: str, request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    definition = BUILTIN_MODULES.get(module_key)
    if not definition:
        raise HTTPException(status_code=404, detail="Modul nicht gefunden")
    state = db.scalar(
        select(ModuleState).where(
            ModuleState.family_id == user.family_id,
            ModuleState.module_key == module_key,
        )
    )
    enabled = state.enabled if state else bool(definition.get("default", False))
    if not enabled:
        raise HTTPException(status_code=404, detail="Modul ist nicht aktiviert")
    permission = str(definition.get("permission", f"{module_key}.read"))
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Modul")
    navigation_modules = [item for item in enabled_modules(db, user.family_id, user) if item.get("menu")]
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    return templates.TemplateResponse(
        request=request,
        name="module_placeholder.html",
        context={
            "user": user,
            "is_admin": is_admin,
            "module": {"key": module_key, **definition},
            "navigation_modules": navigation_modules,
        },
    )
