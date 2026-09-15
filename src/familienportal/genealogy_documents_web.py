from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.genealogy_document_models import GenealogyDocumentLink
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
ALLOWED_PROVIDERS = {"nextcloud", "paperless"}


@router.post("/genealogy/person/{handle}/documents")
def add_document_link(handle: str, request: Request, provider: str = Form(...), external_ref: str = Form(...), title: str = Form(...), category: str = Form(""), db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not has_permission(user, "genealogy.write") and not user.is_superadmin:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    provider = provider.strip().lower()
    if provider not in ALLOWED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unbekannter Dokumentanbieter")
    ref = external_ref.strip().lstrip("/")
    label = title.strip()
    if not ref or not label:
        raise HTTPException(status_code=400, detail="Referenz und Titel sind erforderlich")
    exists = db.scalar(select(GenealogyDocumentLink).where(GenealogyDocumentLink.family_id == user.family_id, GenealogyDocumentLink.person_handle == handle, GenealogyDocumentLink.provider == provider, GenealogyDocumentLink.external_ref == ref))
    if not exists:
        db.add(GenealogyDocumentLink(family_id=user.family_id, person_handle=handle, provider=provider, external_ref=ref, title=label, category=category.strip() or None))
        db.commit()
    return RedirectResponse(f"/genealogy/person/{handle}", status_code=303)
