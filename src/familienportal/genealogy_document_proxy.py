from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.genealogy_document_models import GenealogyDocumentLink
from familienportal.genealogy_privacy import can_view_living, privacy_policy
from familienportal.gramps import GrampsError
from familienportal.gramps_web import _client as gramps_client, _state as gramps_state
from familienportal.nextcloud import NextcloudError
from familienportal.nextcloud_family_scope import family_roots, path_in_roots
from familienportal.nextcloud_web import _client as nextcloud_client, _state as nextcloud_state
from familienportal.paperless import PaperlessError
from familienportal.paperless_web import _client as paperless_client, _state as paperless_state
from familienportal.permissions import has_permission
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)


def _link(link_id: UUID, request: Request, db: Session) -> tuple[object, GenealogyDocumentLink]:
    user = _user_from_session(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    if not has_permission(user, "genealogy.read"):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für Ahnenforschung")
    link = db.scalar(select(GenealogyDocumentLink).where(GenealogyDocumentLink.id == link_id, GenealogyDocumentLink.family_id == user.family_id))
    if not link:
        raise HTTPException(status_code=404, detail="Dokumentverknüpfung nicht gefunden")
    if link.provider not in {"paperless", "nextcloud"}:
        raise HTTPException(status_code=400, detail="Unbekannter Dokumentanbieter")
    state = gramps_state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht aktiviert")
    try:
        person = gramps_client(state).person(link.person_handle)
    except GrampsError as exc:
        raise HTTPException(status_code=502, detail="Datenschutzstatus der Person konnte nicht geprüft werden") from exc
    _, age = privacy_policy(db, user.family_id)
    if not can_view_living(user, person, age):
        raise HTTPException(status_code=404, detail="Dokumentverknüpfung nicht gefunden")
    return user, link


def _document_id(link: GenealogyDocumentLink) -> int:
    try:
        value = int(link.external_ref)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ungültige Paperless-Dokument-ID") from exc
    if value < 1:
        raise HTTPException(status_code=400, detail="Ungültige Paperless-Dokument-ID")
    return value


def _headers(filename: str | None = None) -> dict[str, str]:
    headers = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
    if filename:
        safe_name = filename.replace('"', "").replace("\r", "").replace("\n", "")
        headers["Content-Disposition"] = f'inline; filename="{safe_name}"'
    return headers


def _nextcloud_file(db: Session, user, link: GenealogyDocumentLink):
    state = nextcloud_state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Nextcloud ist nicht aktiviert")
    client = nextcloud_client(state)
    try:
        roots = family_roots(db, user.family_id, client)
        safe_path = path_in_roots(client, link.external_ref, roots)
        return client.get_file(safe_path)
    except NextcloudError as exc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden oder nicht freigegeben") from exc


@router.get("/genealogy/documents/{link_id}/preview")
def preview(link_id: UUID, request: Request, db: Session = Depends(get_db)):
    user, link = _link(link_id, request, db)
    if link.provider == "paperless":
        state = paperless_state(db, user.family_id)
        if not state or not state.enabled:
            raise HTTPException(status_code=409, detail="Paperless-ngx ist nicht aktiviert")
        try:
            result = paperless_client(state).preview(_document_id(link))
        except PaperlessError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return Response(content=result.content, media_type=result.content_type, headers=_headers())
    result = _nextcloud_file(db, user, link)
    if not result.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Für diesen Nextcloud-Dateityp ist keine Bildvorschau verfügbar")
    return Response(content=result.content, media_type=result.content_type, headers=_headers())


@router.get("/genealogy/documents/{link_id}/open")
def open_document(link_id: UUID, request: Request, db: Session = Depends(get_db)):
    user, link = _link(link_id, request, db)
    if link.provider == "paperless":
        state = paperless_state(db, user.family_id)
        if not state or not state.enabled:
            raise HTTPException(status_code=409, detail="Paperless-ngx ist nicht aktiviert")
        try:
            result = paperless_client(state).download(_document_id(link))
        except PaperlessError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return Response(content=result.content, media_type=result.content_type, headers=_headers(result.filename))
    result = _nextcloud_file(db, user, link)
    return Response(content=result.content, media_type=result.content_type, headers=_headers(result.filename))
