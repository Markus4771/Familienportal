from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow_management import provision_mailbox, update_mailbox
from familienportal.mailcow_service import get_mailcow_client
from familienportal.platform_web import _admin

router = APIRouter(prefix="/api/v1/mailcow/mailboxes", tags=["mailcow"])


@router.post("")
def create(request: Request, address: str = Form(...), name: str = Form(...), initial_password: str = Form(...), quota_mb: int = Form(3072), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    provision_mailbox(get_mailcow_client(db, admin.family_id), address=address.strip().lower(), name=name.strip(), password=initial_password, quota_mb=quota_mb)
    return {"status": "created", "mailbox": address.strip().lower()}


@router.post("/{mailbox}/settings")
def settings(mailbox: str, request: Request, name: str = Form(""), quota_mb: int = Form(0), active: bool = Form(True), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    update_mailbox(get_mailcow_client(db, admin.family_id), mailbox, name=name.strip() or None, quota_mb=quota_mb, active=active)
    return {"status": "updated", "mailbox": mailbox}
