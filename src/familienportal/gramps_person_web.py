from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.genealogy_document_models import GenealogyDocumentLink
from familienportal.genealogy_privacy import can_view_living, is_living, redact_living
from familienportal.gramps import GrampsError
from familienportal.gramps_media import media_handles, normalize_media
from familienportal.gramps_relationships import relationship_summary
from familienportal.gramps_web import _client, _state
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
logger = logging.getLogger(__name__)


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
    raw_person = client.person(handle)
    living = is_living(raw_person)
    living_access = can_view_living(user, raw_person)
    person = raw_person if living_access else redact_living(raw_person)
    families = client.all_families()
    people = client.all_people()
    people_by_handle = {str(item.get("handle")): (item if can_view_living(user, item) else redact_living(item)) for item in people if item.get("handle")}
    relations = relationship_summary(person, families, people_by_handle)
    media = []
    document_links = []
    if living_access:
        for media_handle in media_handles(raw_person):
            try:
                media.append(normalize_media(client.media(media_handle)))
            except GrampsError as exc:
                logger.warning("Gramps medium %s could not be loaded: %s", media_handle, exc)
        document_links = list(db.scalars(select(GenealogyDocumentLink).where(GenealogyDocumentLink.family_id == user.family_id, GenealogyDocumentLink.person_handle == handle).order_by(GenealogyDocumentLink.provider, GenealogyDocumentLink.title)))
    return templates.TemplateResponse(request=request, name="genealogy_person.html", context={"user": user, "is_admin": user.is_superadmin, "person": person, "relations": relations, "media": media, "document_links": document_links, "is_living": living, "living_access": living_access, "can_link_documents": living_access and (user.is_superadmin or has_permission(user, "genealogy.write")), "gramps_base_url": state.base_url.rstrip("/") if state.base_url else ""})
