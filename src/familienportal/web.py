from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.api import DEFAULT_ROLES, audit
from familienportal.auth_models import LoginSession
from familienportal.auth_security import create_session, get_mfa_state, valid_session
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import Family, Household, Role, User, UserStatus
from familienportal.platform_runtime import configured_connectors, enabled_modules, family_settings
from familienportal.security import hash_password, verify_password
from familienportal.task_dashboard import task_dashboard

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


def _is_admin(user: User) -> bool:
    return user.is_superadmin or any(role.name == "Administrator" for role in user.roles)


def _user_from_session(request: Request, db: Session) -> User | None:
    value = request.session.get("user_id")
    if not value:
        return None
    try:
        user_id = UUID(value)
        user = db.get(User, user_id)
    except ValueError:
        request.session.clear()
        return None
    if not user or user.status != UserStatus.ACTIVE.value:
        request.session.clear()
        return None
    session_value = request.session.get("session_id")
    if session_value:
        try:
            item = valid_session(db, UUID(session_value), user.id)
        except ValueError:
            item = None
        if not item:
            request.session.clear()
            return None
        db.commit()
    else:
        item = create_session(db, user, settings, request.headers.get("user-agent"))
        request.session["session_id"] = str(item.id)
        db.commit()
    return user


def _context(request: Request, user: User | None = None, **extra: object) -> dict[str, object]:
    return {"user": user, "is_admin": bool(user and _is_admin(user)), **extra}


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    setup_required = (db.scalar(select(func.count()).select_from(User)) or 0) == 0
    if setup_required:
        return RedirectResponse("/setup", status_code=303)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    family = db.get(Family, user.family_id)
    user_count = db.scalar(select(func.count()).select_from(User).where(User.family_id == user.family_id)) or 0
    household_count = db.scalar(select(func.count()).select_from(Household).where(Household.family_id == user.family_id)) or 0
    modules = enabled_modules(db, user.family_id, user)
    connectors = configured_connectors(db, user.family_id)
    portal_settings = family_settings(db, user.family_id)
    tasks = task_dashboard(db, user)
    return templates.TemplateResponse(request=request, name="dashboard.html", context=_context(request, user, family=family, user_count=user_count, household_count=household_count, modules=modules, connectors=connectors, portal_settings=portal_settings, task_dashboard=tasks, navigation_modules=[item for item in modules if item.get("menu")]))


@router.get("/docs")
def docs_redirect():
    return RedirectResponse("/api/docs", status_code=303)
