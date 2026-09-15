from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.auth_models import LoginSession
from familienportal.auth_security import consume_recovery_code, create_session, decrypt_seed, get_mfa_state, valid_session, verify_totp
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import AuditEvent, Family, Household, Role, User, UserStatus
from familienportal.schemas import HouseholdCreate, LoginRequest, SetupRequest, UserCreate
from familienportal.security import hash_password, verify_password

router = APIRouter(prefix="/api/v1")
settings = get_settings()

DEFAULT_ROLES: dict[str, str] = {
    "Administrator": "*",
    "Erwachsene": "dashboard.read,calendar.*,tasks.read,tasks.create,tasks.edit,tasks.assign,tasks.complete,tasks.delete,tasks.manage,documents.read,chat.*",
    "Kind": "dashboard.read,calendar.read,tasks.read,tasks.create,tasks.edit,tasks.complete,chat.use",
    "Gast": "dashboard.read,calendar.read,tasks.read",
}


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    session_id = request.session.get("session_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    try:
        user = db.get(User, UUID(user_id))
    except ValueError:
        user = None
    if not user or user.status != UserStatus.ACTIVE.value:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sitzung ungültig")
    if session_id:
        try:
            session = valid_session(db, UUID(session_id), user.id)
        except ValueError:
            session = None
        if not session:
            request.session.clear()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sitzung ungültig")
        db.commit()
    else:
        session = create_session(db, user, settings, request.headers.get("user-agent"))
        request.session["session_id"] = str(session.id)
        db.commit()
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.is_superadmin or any(role.name == "Administrator" for role in user.roles):
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administratorrecht erforderlich")


def audit(db: Session, action: str, *, actor: User | None = None, family_id: UUID | None = None, target_type: str | None = None, target_id: str | None = None, details: str | None = None) -> None:
    db.add(AuditEvent(family_id=family_id or (actor.family_id if actor else None), actor_user_id=actor.id if actor else None, action=action, target_type=target_type, target_id=target_id, details=details))


@router.get("/setup/status", tags=["setup"])
def setup_status(db: Session = Depends(get_db)) -> dict[str, bool]:
    return {"required": (db.scalar(select(func.count()).select_from(User)) or 0) == 0}


@router.post("/setup", status_code=status.HTTP_201_CREATED, tags=["setup"])
def setup(payload: SetupRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    if (db.scalar(select(func.count()).select_from(User)) or 0) > 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ersteinrichtung bereits abgeschlossen")
    family = Family(name=payload.family_name, slug=payload.family_slug, profile=payload.profile)
    household = Household(name=payload.household_name, family=family)
    db.add_all([family, household])
    db.flush()
    roles = {name: Role(family_id=family.id, name=name, permissions=permissions, system_role=True) for name, permissions in DEFAULT_ROLES.items()}
    db.add_all(roles.values())
    admin = User(family_id=family.id, household_id=household.id, email=str(payload.admin_email).lower(), display_name=payload.admin_name, password_hash=hash_password(payload.admin_password), is_superadmin=True)
    admin.roles.append(roles["Administrator"])
    db.add(admin)
    db.flush()
    session = create_session(db, admin, settings, request.headers.get("user-agent"))
    audit(db, "system.setup.completed", actor=admin, target_type="family", target_id=str(family.id))
    db.commit()
    request.session["user_id"] = str(admin.id)
    request.session["session_id"] = str(session.id)
    return {"status": "created", "family_id": family.id, "user_id": admin.id}


@router.post("/auth/login", tags=["authentication"])
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    user = db.scalar(select(User).where(func.lower(User.email) == str(payload.email).lower()))
    if not user or user.status != UserStatus.ACTIVE.value or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-Mail oder Passwort ist falsch")
    mfa = get_mfa_state(db, user.id)
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    requires_mfa = bool(mfa and mfa.enabled) or bool(settings.require_admin_mfa and is_admin)
    if requires_mfa:
        if not mfa or not mfa.enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Für dieses Konto ist 2FA vorgeschrieben, aber noch nicht eingerichtet")
        request.session.clear()
        request.session["preauth_user_id"] = str(user.id)
        return {"status": "mfa_required"}
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "ok", "user": {"id": user.id, "display_name": user.display_name, "email": user.email}}


@router.post("/auth/mfa", tags=["authentication"])
def login_mfa(request: Request, code: str, db: Session = Depends(get_db)) -> dict[str, object]:
    value = request.session.get("preauth_user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Keine ausstehende 2FA-Anmeldung")
    try:
        user = db.get(User, UUID(value))
    except ValueError:
        user = None
    if not user or user.status != UserStatus.ACTIVE.value:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Anmeldung ungültig")
    mfa = get_mfa_state(db, user.id)
    if not mfa or not mfa.enabled or not mfa.encrypted_seed:
        raise HTTPException(status_code=409, detail="2FA ist nicht verfügbar")
    valid = verify_totp(decrypt_seed(mfa.encrypted_seed, settings), code)
    if not valid:
        valid = consume_recovery_code(mfa, code)
    if not valid:
        raise HTTPException(status_code=401, detail="2FA- oder Recovery-Code ist falsch")
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login.mfa", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "ok", "user": {"id": user.id, "display_name": user.display_name, "email": user.email}}


@router.post("/auth/logout", tags=["authentication"])
def logout(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    value = request.session.get("session_id")
    if value:
        try:
            item = db.get(LoginSession, UUID(value))
        except ValueError:
            item = None
        if item and item.revoked_at is None:
            item.revoked_at = datetime.now(timezone.utc)
            db.commit()
    request.session.clear()
    return {"status": "ok"}


@router.get("/auth/me", tags=["authentication"])
def me(user: User = Depends(current_user)) -> dict[str, object]:
    return {"id": user.id, "family_id": user.family_id, "household_id": user.household_id, "email": user.email, "display_name": user.display_name, "status": user.status, "roles": [role.name for role in user.roles]}


@router.get("/admin/households", tags=["administration"])
def list_households(admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    items = db.scalars(select(Household).where(Household.family_id == admin.family_id).order_by(Household.name)).all()
    return [{"id": item.id, "name": item.name, "description": item.description} for item in items]


@router.post("/admin/households", status_code=status.HTTP_201_CREATED, tags=["administration"])
def create_household(payload: HouseholdCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    item = Household(family_id=admin.family_id, name=payload.name, description=payload.description)
    db.add(item)
    db.flush()
    audit(db, "household.created", actor=admin, target_type="household", target_id=str(item.id))
    db.commit()
    return {"id": item.id, "name": item.name}


@router.get("/admin/users", tags=["administration"])
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    users = db.scalars(select(User).where(User.family_id == admin.family_id).order_by(User.display_name)).unique().all()
    return [{"id": user.id, "email": user.email, "display_name": user.display_name, "status": user.status, "household_id": user.household_id, "roles": [role.name for role in user.roles]} for user in users]


@router.post("/admin/users", status_code=status.HTTP_201_CREATED, tags=["administration"])
def create_user(payload: UserCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.family_id == admin.family_id, func.lower(User.email) == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-Mail ist bereits vorhanden")
    roles = db.scalars(select(Role).where(Role.family_id == admin.family_id, Role.name.in_(payload.role_names))).all() if payload.role_names else []
    user = User(family_id=admin.family_id, household_id=payload.household_id, email=email, display_name=payload.display_name, password_hash=hash_password(payload.password))
    user.roles.extend(roles)
    db.add(user)
    db.flush()
    audit(db, "user.created", actor=admin, target_type="user", target_id=str(user.id))
    db.commit()
    return {"id": user.id, "email": user.email, "display_name": user.display_name}


@router.post("/admin/users/{user_id}/lock", tags=["administration"])
def lock_user(user_id: UUID, admin: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.get(User, user_id)
    if not user or user.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(status_code=409, detail="Das eigene Konto kann hier nicht gesperrt werden")
    user.status = UserStatus.LOCKED.value
    for session in db.scalars(select(LoginSession).where(LoginSession.user_id == user.id, LoginSession.revoked_at.is_(None))).all():
        session.revoked_at = datetime.now(timezone.utc)
    audit(db, "user.locked", actor=admin, target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "locked"}


@router.get("/admin/audit", tags=["administration"])
def list_audit(admin: User = Depends(require_admin), db: Session = Depends(get_db), limit: int = 100) -> list[dict[str, object]]:
    limit = max(1, min(limit, 500))
    events = db.scalars(select(AuditEvent).where(AuditEvent.family_id == admin.family_id).order_by(AuditEvent.created_at.desc()).limit(limit)).all()
    return [{"id": event.id, "action": event.action, "actor_user_id": event.actor_user_id, "target_type": event.target_type, "target_id": event.target_id, "details": event.details, "created_at": event.created_at} for event in events]
