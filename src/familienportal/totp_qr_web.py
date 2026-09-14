from io import BytesIO
from uuid import UUID

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from familienportal.auth_security import decrypt_seed, get_mfa_state, otpauth_uri
from familienportal.config import get_settings
from familienportal.database import get_db
from familienportal.models import User, UserStatus

router = APIRouter(include_in_schema=False)
settings = get_settings()


@router.get("/security/mfa/qr")
def mfa_qr(request: Request, db: Session = Depends(get_db)):
    value = request.session.get("user_id")
    if not value:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    user = db.get(User, UUID(value))
    if not user or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(status_code=401, detail="Ungültige Sitzung")
    state = get_mfa_state(db, user.id)
    if not state or not state.encrypted_seed:
        raise HTTPException(status_code=404, detail="Keine laufende 2FA-Einrichtung")
    uri = otpauth_uri(user, decrypt_seed(state.encrypted_seed, settings), settings)
    image = qrcode.make(uri)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png", headers={"Cache-Control": "no-store"})
