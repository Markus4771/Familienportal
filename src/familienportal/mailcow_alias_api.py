from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow_management import add_alias
from familienportal.mailcow_service import get_mailcow_client
from familienportal.platform_web import _admin

router = APIRouter(prefix="/api/v1/mailcow/aliases", tags=["mailcow"])


@router.post("")
def create(request: Request, address: str = Form(...), destination: str = Form(...), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    add_alias(get_mailcow_client(db, admin.family_id), address.strip().lower(), destination.strip().lower())
    return {"status": "created", "alias": address.strip().lower()}


@router.post("/{alias_id}/settings")
def settings(alias_id: str, request: Request, destination: str = Form(...), active: bool = Form(True), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    get_mailcow_client(db, admin.family_id).edit_alias(alias_id, destination=destination, active=active)
    return {"status": "updated", "alias_id": alias_id}
