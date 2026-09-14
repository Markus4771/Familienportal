from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.calendar_models import CalendarEvent
from familienportal.calendar_sync_models import CalendarEventSyncState, CalendarSyncBinding
from familienportal.database import get_db
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/calendar/conflicts", response_class=HTMLResponse)
def conflict_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    states = db.scalars(
        select(CalendarEventSyncState)
        .join(CalendarSyncBinding)
        .where(CalendarSyncBinding.family_id == admin.family_id, CalendarEventSyncState.conflict.is_(True))
    ).all()
    items = []
    for state in states:
        event = db.get(CalendarEvent, state.event_id)
        items.append({"event": event, "state": state})
    return templates.TemplateResponse(request=request, name="calendar_conflicts.html", context={"user": admin, "is_admin": True, "items": items})
