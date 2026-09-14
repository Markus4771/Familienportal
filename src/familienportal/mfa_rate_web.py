from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.auth_security import consume_recovery_code, create_session, decrypt_seed, get_mfa_state, verify_totp
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.throttle import clear, fail, lock_seconds

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


@router.post("/mfa", response_class=HTMLResponse)
def mfa(request: Request, code: str = Form(...), db: Session = Depends(get_db)):
    value = request.session.get("preauth_user_id")
    key = request.session.get("mfa_throttle_key")
    if not value:
        return RedirectResponse("/login", status_code=303)
    if key:
        wait = lock_seconds(db, key)
        if wait:
            db.commit()
            return templates.TemplateResponse(request=request, name="mfa_login.html", context={"user": None, "is_admin": False, "error": f"Zu viele Versuche. Bitte in {wait} Sekunden erneut versuchen."}, status_code=429)
    user = db.get(User, UUID(value))
    state = get_mfa_state(db, user.id) if user else None
    valid = bool(user and user.status == UserStatus.ACTIVE.value and state and state.enabled and state.encrypted_seed and (verify_totp(decrypt_seed(state.encrypted_seed, settings), code) or consume_recovery_code(state, code)))
    if not valid:
        if key:
            fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
        db.commit()
        return templates.TemplateResponse(request=request, name="mfa_login.html", context={"user": None, "is_admin": False, "error": "Der 2FA- oder Recovery-Code ist ungültig."}, status_code=401)
    if key:
        clear(db, key)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login.mfa", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)
