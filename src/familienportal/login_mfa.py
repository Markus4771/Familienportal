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

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


@router.get("/mfa", response_class=HTMLResponse)
def mfa_page(request: Request):
    if not request.session.get("preauth_user_id"):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="mfa_login.html", context={"user": None, "is_admin": False})


@router.post("/mfa", response_class=HTMLResponse)
def mfa_submit(request: Request, code: str = Form(...), db: Session = Depends(get_db)):
    value = request.session.get("preauth_user_id")
    if not value:
        return RedirectResponse("/login", status_code=303)
    try:
        user = db.get(User, UUID(value))
    except ValueError:
        user = None
    if not user or user.status != UserStatus.ACTIVE.value:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)
    state = get_mfa_state(db, user.id)
    valid = False
    if state and state.enabled and state.encrypted_seed:
        valid = verify_totp(decrypt_seed(state.encrypted_seed, settings), code)
        if not valid:
            valid = consume_recovery_code(state, code)
    if not valid:
        return templates.TemplateResponse(request=request, name="mfa_login.html", context={"user": None, "is_admin": False, "error": "Der 2FA- oder Recovery-Code ist ungültig."}, status_code=401)
    request.session.clear()
    session = create_session(db, user, settings, request.headers.get("user-agent"))
    request.session["user_id"] = str(user.id)
    request.session["session_id"] = str(session.id)
    user.last_login_at = datetime.now(timezone.utc)
    audit(db, "auth.login.mfa", actor=user, target_type="user", target_id=str(user.id))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)
