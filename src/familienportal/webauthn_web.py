from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from webauthn.helpers.exceptions import WebAuthnException

from familienportal.api import audit
from familienportal.auth_models import PasskeyCredential
from familienportal.auth_security import create_session
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.throttle import clear, fail, lock_seconds, make_key
from familienportal.webauthn_service import (
    authentication_options,
    finish_authentication,
    finish_registration,
    passkeys_for_user,
    registration_options,
)

router = APIRouter(include_in_schema=False)
settings = get_settings()


def _current_user(request: Request, db: Session) -> User:
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    try:
        user = db.get(User, UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung") from exc
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    return user


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/api/v1/security/passkeys/register/options")
def passkey_register_options(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    options, challenge = registration_options(db, user, settings)
    request.session["webauthn_registration_challenge"] = challenge
    return options


@router.post("/api/v1/security/passkeys/register/verify")
async def passkey_register_verify(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    challenge = request.session.pop("webauthn_registration_challenge", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="Registrierung ist abgelaufen")
    body = await request.json()
    credential = body.get("credential") or {}
    label = str(body.get("label") or "Passkey")
    try:
        item = finish_registration(db, user, settings, credential, challenge, label)
    except (WebAuthnException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Passkey konnte nicht registriert werden: {exc}") from exc
    audit(db, "security.passkey.created", actor=user, target_type="passkey", target_id=str(item.id))
    db.commit()
    return {"status": "created", "id": str(item.id), "label": item.label}


@router.post("/security/passkeys/{credential_id}/delete")
def passkey_delete(credential_id: UUID, request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    item = db.get(PasskeyCredential, credential_id)
    if item and item.user_id == user.id:
        db.delete(item)
        audit(db, "security.passkey.deleted", actor=user, target_type="passkey", target_id=str(item.id))
        db.commit()
    return RedirectResponse("/security", status_code=303)


@router.post("/api/v1/auth/passkey/options")
async def passkey_login_options(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    email = str(body.get("email") or "").strip().lower()
    key = make_key("passkey", email, _client_ip(request))
    wait = lock_seconds(db, key)
    if wait:
        db.commit()
        return JSONResponse({"detail": "Zu viele Anmeldeversuche", "retry_after": wait}, status_code=429, headers={"Retry-After": str(wait)})
    user = db.scalar(select(User).where(func.lower(User.email) == email, User.status == UserStatus.ACTIVE.value))
    if not user or not passkeys_for_user(db, user.id):
        fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
        db.commit()
        raise HTTPException(status_code=401, detail="Passkey-Anmeldung nicht verfügbar")
    options, challenge = authentication_options(db, user, settings)
    request.session.clear()
    request.session["passkey_user_id"] = str(user.id)
    request.session["webauthn_authentication_challenge"] = challenge
    request.session["passkey_throttle_key"] = key
    return options


@router.post("/api/v1/auth/passkey/verify")
async def passkey_login_verify(request: Request, db: Session = Depends(get_db)):
    user_value = request.session.get("passkey_user_id")
    challenge = request.session.get("webauthn_authentication_challenge")
    key = request.session.get("passkey_throttle_key")
    if not user_value or not challenge:
        raise HTTPException(status_code=400, detail="Passkey-Anmeldung ist abgelaufen")
    user = db.get(User, UUID(user_value))
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Anmeldung nicht möglich")
    credential = await request.json()
    try:
        item = finish_authentication(db, user, settings, credential, challenge)
    except (WebAuthnException, ValueError) as exc:
        if key:
            wait = fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
            db.commit()
            if wait:
                return JSONResponse({"detail": "Zu viele Anmeldeversuche", "retry_after": wait}, status_code=429, headers={"Retry-After": str(wait)})
        raise HTTPException(status_code=401, detail="Passkey konnte nicht bestätigt werden") from exc
    if key:
        clear(db, key)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login.passkey", actor=user, target_type="passkey", target_id=str(item.id))
    db.commit()
    return {"status": "ok", "redirect": "/dashboard"}
