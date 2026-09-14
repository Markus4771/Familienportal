from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.auth_security import consume_recovery_code, create_session, decrypt_seed, get_mfa_state, verify_totp
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.schemas import LoginRequest
from familienportal.security import verify_password
from familienportal.throttle import clear, fail, lock_seconds, make_key

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
settings = get_settings()


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    normalized = str(payload.email).lower()
    key = make_key("password", normalized, request.client.host if request.client else None)
    wait = lock_seconds(db, key)
    if wait:
        db.commit()
        raise HTTPException(status_code=429, detail="Zu viele Anmeldeversuche", headers={"Retry-After": str(wait)})
    user = db.scalar(select(User).where(func.lower(User.email) == normalized))
    if not user or user.status != UserStatus.ACTIVE.value or not verify_password(payload.password, user.password_hash):
        fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
        db.commit()
        raise HTTPException(status_code=401, detail="E-Mail oder Passwort ist falsch")
    clear(db, key)
    mfa = get_mfa_state(db, user.id)
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    if (mfa and mfa.enabled) or (settings.require_admin_mfa and is_admin):
        if not mfa or not mfa.enabled:
            db.commit()
            raise HTTPException(status_code=403, detail="2FA ist vorgeschrieben, aber noch nicht eingerichtet")
        request.session.clear()
        request.session["preauth_user_id"] = str(user.id)
        request.session["mfa_throttle_key"] = make_key("mfa", str(user.id), request.client.host if request.client else None)
        db.commit()
        return {"status": "mfa_required"}
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "ok"}


@router.post("/mfa")
def mfa(request: Request, code: str, db: Session = Depends(get_db)):
    value = request.session.get("preauth_user_id")
    key = request.session.get("mfa_throttle_key")
    if not value:
        raise HTTPException(status_code=401, detail="Keine ausstehende 2FA-Anmeldung")
    if key:
        wait = lock_seconds(db, key)
        if wait:
            db.commit()
            raise HTTPException(status_code=429, detail="Zu viele 2FA-Versuche", headers={"Retry-After": str(wait)})
    user = db.get(User, UUID(value))
    state = get_mfa_state(db, user.id) if user else None
    valid = bool(user and state and state.enabled and state.encrypted_seed and (verify_totp(decrypt_seed(state.encrypted_seed, settings), code) or consume_recovery_code(state, code)))
    if not valid:
        if key:
            fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
        db.commit()
        raise HTTPException(status_code=401, detail="2FA- oder Recovery-Code ist ungültig")
    if key:
        clear(db, key)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login.mfa", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return {"status": "ok"}
