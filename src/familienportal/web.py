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


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    if (db.scalar(select(func.count()).select_from(User)) or 0) > 0:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="setup.html", context=_context(request))


@router.post("/setup")
def setup_submit(
    request: Request,
    family_name: str = Form(...),
    family_slug: str = Form(...),
    household_name: str = Form(...),
    profile: str = Form("small_family"),
    admin_name: str = Form(...),
    admin_email: str = Form(...),
    admin_password: str = Form(...),
    db: Session = Depends(get_db),
):
    if (db.scalar(select(func.count()).select_from(User)) or 0) > 0:
        return RedirectResponse("/login", status_code=303)
    if len(admin_password) < 10:
        return templates.TemplateResponse(request=request, name="setup.html", context=_context(request, error="Das Passwort muss mindestens 10 Zeichen lang sein."), status_code=400)
    family = Family(name=family_name.strip(), slug=family_slug.strip().lower(), profile=profile)
    household = Household(name=household_name.strip(), family=family)
    db.add_all([family, household])
    db.flush()
    roles = {name: Role(family_id=family.id, name=name, permissions=permissions, system_role=True) for name, permissions in DEFAULT_ROLES.items()}
    db.add_all(roles.values())
    admin = User(family_id=family.id, household_id=household.id, email=admin_email.strip().lower(), display_name=admin_name.strip(), password_hash=hash_password(admin_password), is_superadmin=True)
    admin.roles.append(roles["Administrator"])
    db.add(admin)
    db.flush()
    session = create_session(db, admin, settings, request.headers.get("user-agent"))
    audit(db, "system.setup.completed", actor=admin, target_type="family", target_id=str(family.id))
    db.commit()
    request.session["user_id"] = str(admin.id)
    request.session["session_id"] = str(session.id)
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if _user_from_session(request, db):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context=_context(request))


@router.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if not user or user.status != UserStatus.ACTIVE.value or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context=_context(request, error="E-Mail-Adresse oder Passwort ist falsch."), status_code=401)
    mfa = get_mfa_state(db, user.id)
    requires_mfa = bool(mfa and mfa.enabled) or bool(settings.require_admin_mfa and _is_admin(user))
    if requires_mfa:
        if not mfa or not mfa.enabled:
            return templates.TemplateResponse(request=request, name="login.html", context=_context(request, error="Für Administratoren ist 2FA vorgeschrieben. Bitte 2FA zunächst über eine bestehende Sitzung aktivieren."), status_code=403)
        request.session.clear()
        request.session["preauth_user_id"] = str(user.id)
        return RedirectResponse("/mfa", status_code=303)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    session_value = request.session.get("session_id")
    if session_value:
        try:
            item = db.get(LoginSession, UUID(session_value))
        except ValueError:
            item = None
        if item and item.revoked_at is None:
            item.revoked_at = datetime.now(timezone.utc)
            db.commit()
    request.session.clear()
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
    return templates.TemplateResponse(request=request, name="dashboard.html", context=_context(request, user, family=family, user_count=user_count, household_count=household_count, modules=modules, connectors=connectors, portal_settings=portal_settings, navigation_modules=[item for item in modules if item.get("menu")]))


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Administratorrecht erforderlich")
    users = db.scalars(select(User).where(User.family_id == user.family_id).order_by(User.display_name)).unique().all()
    households = db.scalars(select(Household).where(Household.family_id == user.family_id).order_by(Household.name)).all()
    roles = db.scalars(select(Role).where(Role.family_id == user.family_id).order_by(Role.name)).all()
    return templates.TemplateResponse(request=request, name="admin.html", context=_context(request, user, users=users, households=households, roles=roles))


@router.post("/admin/households")
def admin_add_household(request: Request, name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    admin = _user_from_session(request, db)
    if not admin or not _is_admin(admin):
        return RedirectResponse("/login", status_code=303)
    item = Household(family_id=admin.family_id, name=name.strip(), description=description.strip() or None)
    db.add(item)
    db.flush()
    audit(db, "household.created", actor=admin, target_type="household", target_id=str(item.id))
    db.commit()
    return RedirectResponse("/admin#households", status_code=303)


@router.post("/admin/users")
def admin_add_user(request: Request, display_name: str = Form(...), email: str = Form(...), password: str = Form(...), household_id: str = Form(""), role_name: str = Form("Erwachsene"), db: Session = Depends(get_db)):
    admin = _user_from_session(request, db)
    if not admin or not _is_admin(admin):
        return RedirectResponse("/login", status_code=303)
    normalized_email = email.strip().lower()
    if db.scalar(select(User).where(User.family_id == admin.family_id, func.lower(User.email) == normalized_email)):
        return RedirectResponse("/admin?error=Benutzer+existiert+bereits", status_code=303)
    role = db.scalar(select(Role).where(Role.family_id == admin.family_id, Role.name == role_name))
    item = User(family_id=admin.family_id, household_id=UUID(household_id) if household_id else None, email=normalized_email, display_name=display_name.strip(), password_hash=hash_password(password))
    if role:
        item.roles.append(role)
    db.add(item)
    db.flush()
    audit(db, "user.created", actor=admin, target_type="user", target_id=str(item.id))
    db.commit()
    return RedirectResponse("/admin#users", status_code=303)
