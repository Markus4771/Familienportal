from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.auth_security import create_session, get_mfa_state
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.security import verify_password
from familienportal.throttle import clear, fail, lock_seconds, make_key

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    normalized = email.strip().lower()
    key = make_key("password", normalized, request.client.host if request.client else None)
    wait = lock_seconds(db, key)
    if wait:
        db.commit()
        return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "is_admin": False, "error": f"Zu viele Anmeldeversuche. Bitte in {wait} Sekunden erneut versuchen."}, status_code=429)
    user = db.scalar(select(User).where(func.lower(User.email) == normalized))
    if not user or user.status != UserStatus.ACTIVE.value or not verify_password(password, user.password_hash):
        fail(db, key, maximum=settings.login_max_failures, window_minutes=settings.login_window_minutes, lock_minutes=settings.login_lock_minutes)
        db.commit()
        return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "is_admin": False, "error": "E-Mail-Adresse oder Passwort ist falsch."}, status_code=401)
    clear(db, key)
    mfa = get_mfa_state(db, user.id)
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    if (mfa and mfa.enabled) or (settings.require_admin_mfa and is_admin):
        if not mfa or not mfa.enabled:
            db.commit()
            return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "is_admin": False, "error": "Für Administratoren ist 2FA vorgeschrieben, aber noch nicht eingerichtet."}, status_code=403)
        request.session.clear()
        request.session["preauth_user_id"] = str(user.id)
        request.session["mfa_throttle_key"] = make_key("mfa", str(user.id), request.client.host if request.client else None)
        db.commit()
        return RedirectResponse("/mfa", status_code=303)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)
