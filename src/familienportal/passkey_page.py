from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.models import User, UserStatus
from familienportal.webauthn_service import passkeys_for_user

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/security/passkeys", response_class=HTMLResponse)
def page(request: Request, db: Session = Depends(get_db)):
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    user = db.get(User, UUID(value))
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    return templates.TemplateResponse(request=request, name="security_passkeys.html", context={
        "user": user,
        "is_admin": user.is_superadmin or any(role.name == "Administrator" for role in user.roles),
        "passkeys": passkeys_for_user(db, user.id),
    })
