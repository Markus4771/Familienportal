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

# Default family roles. Task permissions are deliberately explicit instead of
# tasks.* so child/guest capabilities stay understandable and configurable.
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
        user_uuid = UUID(user_id)
        user = db.get(User, user_uuid)
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
