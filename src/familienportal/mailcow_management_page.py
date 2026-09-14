from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow import MailcowError
from familienportal.mailcow_models import MailcowUserMapping
from familienportal.mailcow_service import get_mailcow_summary
from familienportal.models import User
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/platform/mailcow/management", response_class=HTMLResponse)
def management_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    data = {"domains": [], "mailboxes": [], "aliases": [], "quota_used": 0, "quota_limit": 0}
    error = None
    try:
        data = get_mailcow_summary(db, admin.family_id)
    except MailcowError as exc:
        error = str(exc)
    users = db.scalars(select(User).where(User.family_id == admin.family_id).order_by(User.display_name)).all()
    mappings = db.scalars(select(MailcowUserMapping).where(MailcowUserMapping.family_id == admin.family_id)).all()
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == admin.family_id, ConnectorState.connector_key == "mailcow"))
    return templates.TemplateResponse(request=request, name="mailcow_management.html", context={
        "user": admin,
        "is_admin": True,
        "data": data,
        "error": error,
        "users": users,
        "mappings": {item.user_id: item for item in mappings},
        "sogo_url": f"{state.base_url.rstrip('/')}/SOGo/" if state and state.base_url else None,
    })
