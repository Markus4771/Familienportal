from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.caldav import CalDAVClient, CalDAVError
from familienportal.database import get_db
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin
from familienportal.secrets import read_secret

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/calendar/caldav", response_class=HTMLResponse)
def caldav_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == admin.family_id, ConnectorState.connector_key == "nextcloud"))
    ok = False
    message = "Nextcloud ist nicht vollständig konfiguriert."
    calendars: list[dict[str, str]] = []
    if state and state.enabled and state.base_url and state.username and state.secret_reference:
        password = read_secret(state.secret_reference)
        if password:
            client = CalDAVClient(state.base_url, state.username, password)
            ok, message = client.test()
            if ok:
                try:
                    calendars = client.list_calendars()
                except CalDAVError as exc:
                    message = f"{message} Kalenderliste: {exc}"
    return templates.TemplateResponse(request=request, name="calendar_caldav.html", context={"user": admin, "is_admin": True, "ok": ok, "message": message, "calendars": calendars})
