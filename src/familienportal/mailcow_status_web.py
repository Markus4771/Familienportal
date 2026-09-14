from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.mailcow import MailcowClient
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin
from familienportal.secrets import read_secret

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/platform/mailcow", response_class=HTMLResponse)
def mailcow_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == admin.family_id, ConnectorState.connector_key == "mailcow"))
    data = {"domains": [], "mailboxes": [], "aliases": [], "quota_used": 0, "quota_limit": 0}
    error = None
    if state and state.enabled and state.base_url and state.secret_reference:
        api_key = read_secret(state.secret_reference)
        if api_key:
            try:
                data = MailcowClient(state.base_url, api_key).summary()
            except Exception as exc:
                error = str(exc)
        else:
            error = "Mailcow API-Key nicht verfügbar."
    return templates.TemplateResponse(request=request, name="mailcow.html", context={"user": admin, "is_admin": True, "state": state, "data": data, "error": error})
