from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow_management import remove_user_mapping, save_user_mapping
from familienportal.platform_web import _admin

router = APIRouter(prefix="/api/v1/mailcow", tags=["mailcow"])


@router.post("/mapping")
def mapping(request: Request, user_id: UUID = Form(...), mailbox: str = Form(...), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    item = save_user_mapping(db, admin.family_id, user_id, mailbox)
    db.commit()
    return {"id": item.id, "user_id": item.user_id, "mailbox": item.mailbox}


@router.post("/mapping/{user_id}/delete")
def delete_mapping(user_id: UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    removed = remove_user_mapping(db, admin.family_id, user_id)
    db.commit()
    return {"status": "deleted" if removed else "not_found", "user_id": user_id}
