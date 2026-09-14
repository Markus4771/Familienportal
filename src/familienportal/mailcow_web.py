from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow import MailcowError
from familienportal.mailcow_service import get_mailcow_summary
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/platform/mailcow", response_class=HTMLResponse)
def mailcow_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    data = {"domains": [], "mailboxes": [], "aliases": [], "quota_used": 0, "quota_limit": 0}
    error = None
    try:
        data = get_mailcow_summary(db, admin.family_id)
    except MailcowError as exc:
        error = str(exc)
    return templates.TemplateResponse(request=request, name="mailcow.html", context={"user": admin, "is_admin": True, "data": data, "error": error})
