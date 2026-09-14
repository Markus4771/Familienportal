from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.gramps_relationships import relationship_summary
from familienportal.gramps_web import _client, _state
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/genealogy/person/{handle}", response_class=HTMLResponse)
def person_detail(handle: str, request: Request, db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not has_permission(user, "genealogy.read"):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Ahnenforschung")
    state = _state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")

    client = _client(state)
    person = client.person(handle)
    families = client.families(pagesize=200)
    people = client.people(pagesize=200)
    people_by_handle = {str(item.get("handle")): item for item in people if item.get("handle")}
    relations = relationship_summary(person, families, people_by_handle)

    return templates.TemplateResponse(
        request=request,
        name="genealogy_person.html",
        context={
            "user": user,
            "is_admin": user.is_superadmin,
            "person": person,
            "relations": relations,
            "gramps_base_url": state.base_url.rstrip("/") if state.base_url else "",
        },
    )
