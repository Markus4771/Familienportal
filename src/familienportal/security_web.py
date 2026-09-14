from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.auth_models import LoginSession, UserMfaState
from familienportal.auth_security import (
    consume_recovery_code,
    consume_recovery_request,
    create_recovery_request,
    decrypt_seed,
    encrypt_seed,
    generate_recovery_codes,
    get_mfa_state,
    new_totp_seed,
    otpauth_uri,
    revoke_all_sessions,
    store_recovery_codes,
    verify_totp,
)
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.security import hash_password
from familienportal.smtp_mailer import MailDeliveryError, send_mail

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


def _user(request: Request, db: Session) -> User:
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


@router.get("/security", response_class=HTMLResponse)
def security_page(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    mfa = get_mfa_state(db, user.id)
    sessions = db.scalars(select(LoginSession).where(LoginSession.user_id == user.id).order_by(LoginSession.created_at.desc())).all()
    return templates.TemplateResponse(request=request, name="security.html", context={
        "user": user,
        "is_admin": user.is_superadmin or any(role.name == "Administrator" for role in user.roles),
        "mfa": mfa,
        "sessions": sessions,
        "current_session_id": request.session.get("session_id"),
        "require_admin_mfa": settings.require_admin_mfa,
    })


@router.post("/security/mfa/start", response_class=HTMLResponse)
def mfa_start(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    seed = new_totp_seed()
    state = get_mfa_state(db, user.id)
    if not state:
        state = UserMfaState(user_id=user.id)
        db.add(state)
    state.encrypted_seed = encrypt_seed(seed, settings)
    state.enabled = False
    state.recovery_hashes_json = "[]"
    state.updated_at = datetime.now(timezone.utc)
    db.commit()
    return templates.TemplateResponse(request=request, name="security_mfa_setup.html", context={
        "user": user,
        "is_admin": user.is_superadmin,
        "seed": seed,
        "otpauth_uri": otpauth_uri(user, seed, settings),
    })


@router.post("/security/mfa/confirm", response_class=HTMLResponse)
def mfa_confirm(request: Request, code: str = Form(...), db: Session = Depends(get_db)):
    user = _user(request, db)
    state = get_mfa_state(db, user.id)
    if not state or not state.encrypted_seed:
        return RedirectResponse("/security", status_code=303)
    seed = decrypt_seed(state.encrypted_seed, settings)
    if not verify_totp(seed, code):
        return templates.TemplateResponse(request=request, name="security_mfa_setup.html", context={
            "user": user,
            "is_admin": user.is_superadmin,
            "seed": seed,
            "otpauth_uri": otpauth_uri(user, seed, settings),
            "error": "Der Bestätigungscode ist ungültig.",
        }, status_code=400)
    recovery_codes = generate_recovery_codes()
    store_recovery_codes(state, recovery_codes)
    state.enabled = True
    state.updated_at = datetime.now(timezone.utc)
    audit(db, "security.mfa.enabled", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return templates.TemplateResponse(request=request, name="security_recovery_codes.html", context={
        "user": user,
        "is_admin": user.is_superadmin,
        "codes": recovery_codes,
    })


@router.post("/security/mfa/disable")
def mfa_disable(request: Request, code: str = Form(...), db: Session = Depends(get_db)):
    user = _user(request, db)
    state = get_mfa_state(db, user.id)
    if not state or not state.enabled or not state.encrypted_seed:
        return RedirectResponse("/security", status_code=303)
    valid = verify_totp(decrypt_seed(state.encrypted_seed, settings), code) or consume_recovery_code(state, code)
    if not valid:
        return RedirectResponse("/security?error=2FA-Code+ungueltig", status_code=303)
    state.enabled = False
    state.encrypted_seed = None
    state.recovery_hashes_json = "[]"
    revoke_all_sessions(db, user.id, except_session_id=UUID(request.session["session_id"]) if request.session.get("session_id") else None)
    audit(db, "security.mfa.disabled", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return RedirectResponse("/security", status_code=303)


@router.post("/security/recovery-codes", response_class=HTMLResponse)
def regenerate_recovery_codes(request: Request, code: str = Form(...), db: Session = Depends(get_db)):
    user = _user(request, db)
    state = get_mfa_state(db, user.id)
    if not state or not state.enabled or not state.encrypted_seed:
        return RedirectResponse("/security", status_code=303)
    if not verify_totp(decrypt_seed(state.encrypted_seed, settings), code):
        return RedirectResponse("/security?error=2FA-Code+ungueltig", status_code=303)
    codes = generate_recovery_codes()
    store_recovery_codes(state, codes)
    audit(db, "security.recovery_codes.regenerated", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return templates.TemplateResponse(request=request, name="security_recovery_codes.html", context={"user": user, "is_admin": user.is_superadmin, "codes": codes})


@router.post("/security/sessions/{session_id}/revoke")
def revoke_session(session_id: UUID, request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    item = db.get(LoginSession, session_id)
    if item and item.user_id == user.id:
        item.revoked_at = datetime.now(timezone.utc)
        audit(db, "security.session.revoked", actor=user, target_type="session", target_id=str(item.id))
        db.commit()
        if str(item.id) == request.session.get("session_id"):
            request.session.clear()
            return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/security", status_code=303)


@router.post("/security/sessions/revoke-others")
def revoke_other_sessions(request: Request, db: Session = Depends(get_db)):
    user = _user(request, db)
    current = UUID(request.session["session_id"]) if request.session.get("session_id") else None
    count = revoke_all_sessions(db, user.id, except_session_id=current)
    audit(db, "security.sessions.revoked", actor=user, target_type="user", target_id=str(user.id), details=f"count={count}")
    db.commit()
    return RedirectResponse("/security", status_code=303)


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={"user": None, "is_admin": False})


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password_submit(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower(), User.status == UserStatus.ACTIVE.value))
    if user:
        token = create_recovery_request(db, user, settings)
        reset_url = f"{settings.public_url}/reset-password?token={token}"
        try:
            send_mail(settings, user.email, "Passwort für Familienportal zurücksetzen", f"Zum Zurücksetzen des Passworts diesen Link öffnen:\n\n{reset_url}\n\nDer Link ist nur begrenzt gültig.")
            audit(db, "security.password_reset.requested", actor=user, target_type="user", target_id=str(user.id))
        except MailDeliveryError:
            audit(db, "security.password_reset.delivery_failed", actor=user, target_type="user", target_id=str(user.id))
        db.commit()
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={"user": None, "is_admin": False, "sent": True})


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"user": None, "is_admin": False, "token": token})


@router.post("/reset-password", response_class=HTMLResponse)
def reset_password_submit(request: Request, token: str = Form(...), password: str = Form(...), password2: str = Form(...), db: Session = Depends(get_db)):
    if password != password2 or len(password) < 10:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"user": None, "is_admin": False, "token": token, "error": "Passwörter stimmen nicht überein oder sind zu kurz."}, status_code=400)
    recovery = consume_recovery_request(db, token)
    if not recovery:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"user": None, "is_admin": False, "token": "", "error": "Der Link ist ungültig oder abgelaufen."}, status_code=400)
    user = db.get(User, recovery.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.password_hash = hash_password(password)
    revoke_all_sessions(db, user.id)
    audit(db, "security.password_reset.completed", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    request.session.clear()
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"user": None, "is_admin": False, "token": "", "completed": True})
