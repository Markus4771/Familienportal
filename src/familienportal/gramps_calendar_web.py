from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.gramps_calendar_sync import sync_gramps_calendar
from familienportal.gramps_web import _client, _state
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)


@router.post("/platform/gramps/calendar-sync")
def sync_calendar(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    people = _client(state).people(pagesize=200)
    result = sync_gramps_calendar(db, admin.family_id, people)
    audit(db, "gramps.calendar.synced", actor=admin, target_type="connector", target_id="gramps", details=str(result))
    db.commit()
    query = "&".join(f"{key}={value}" for key, value in result.items())
    return RedirectResponse(f"/platform/gramps?calendar_sync=1&{query}#calendar-sync", status_code=303)
