from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.auth_models import UserMfaState
from familienportal.auth_security import consume_recovery_code, decrypt_seed, get_mfa_state, revoke_all_sessions, verify_totp
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.security import verify_password

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
settings = get_settings()


def _admin(request: Request, db: Session) -> User:
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    user = db.get(User, UUID(value))
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    if not (user.is_superadmin or any(role.name == "Administrator" for role in user.roles)):
        raise HTTPException(status_code=403, detail="Administratorrecht erforderlich")
    return user


@router.get("/admin/security/mfa-reset", response_class=HTMLResponse)
def reset_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    users = db.scalars(select(User).where(User.family_id == admin.family_id).order_by(User.display_name)).all()
    return templates.TemplateResponse(request=request, name="admin_mfa_reset.html", context={"user": admin, "is_admin": True, "users": users})


@router.post("/admin/security/mfa-reset")
def reset_mfa(request: Request, target_user_id: UUID = Form(...), admin_password: str = Form(...), admin_code: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    if not verify_password(admin_password, admin.password_hash):
        return RedirectResponse("/admin/security/mfa-reset?error=Administrator-Passwort+ungueltig", status_code=303)
    admin_mfa = get_mfa_state(db, admin.id)
    if admin_mfa and admin_mfa.enabled and admin_mfa.encrypted_seed:
        valid = verify_totp(decrypt_seed(admin_mfa.encrypted_seed, settings), admin_code) or consume_recovery_code(admin_mfa, admin_code)
        if not valid:
            return RedirectResponse("/admin/security/mfa-reset?error=Administrator-2FA-Code+ungueltig", status_code=303)
    target = db.get(User, target_user_id)
    if not target or target.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    state = get_mfa_state(db, target.id)
    if state:
        state.enabled = False
        state.encrypted_seed = None
        state.recovery_hashes_json = "[]"
    revoked = revoke_all_sessions(db, target.id)
    audit(db, "security.mfa.admin_reset", actor=admin, target_type="user", target_id=str(target.id), details=f"revoked_sessions={revoked}")
    db.commit()
    return RedirectResponse("/admin/security/mfa-reset?success=1", status_code=303)
