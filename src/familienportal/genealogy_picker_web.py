from __future__ import annotations

from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.nextcloud import NextcloudError
from familienportal.nextcloud_family_scope import family_roots, path_in_roots, picker_path
from familienportal.nextcloud_web import _client as nextcloud_client, _state as nextcloud_state
from familienportal.paperless import PaperlessClient, PaperlessError
from familienportal.permissions import has_permission
from familienportal.platform_models import ConnectorState
from familienportal.secrets import read_secret
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _writer(request: Request, db: Session):
    user = _user_from_session(request, db)
    if not user:
        return None
    if not user.is_superadmin and not has_permission(user, "genealogy.write"):
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
    return user


def _paperless_state(db: Session, family_id):
    return db.scalar(select(ConnectorState).where(ConnectorState.family_id == family_id, ConnectorState.connector_key == "paperless"))


def _paperless_client(state: ConnectorState) -> PaperlessClient:
    if not state.base_url or not state.secret_reference:
        raise HTTPException(status_code=409, detail="Paperless-ngx ist nicht vollständig konfiguriert")
    token = read_secret(state.secret_reference)
    if not token:
        raise HTTPException(status_code=409, detail="Paperless-Secret ist nicht verfügbar")
    return PaperlessClient(state.base_url, token)


@router.get("/genealogy/person/{handle}/picker/nextcloud", response_class=HTMLResponse)
def nextcloud_picker(handle: str, request: Request, path: str = Query(""), db: Session = Depends(get_db)):
    user = _writer(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    state = nextcloud_state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Nextcloud ist nicht aktiviert")
    client = nextcloud_client(state)
    try:
        roots = family_roots(db, user.family_id, client)
        current = picker_path(client, path, roots)
        items = client.list_files(current)
        root = client._dav_path("")
    except NextcloudError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    rows = []
    for item in items:
        href = str(item.get("href") or "")
        decoded = unquote(urlparse(href).path)
        base = unquote(root).rstrip("/") + "/"
        relative = decoded.split(base, 1)[-1].strip("/") if base in decoded else ""
        if not relative or relative == current:
            continue
        try:
            relative = path_in_roots(client, relative, roots)
        except NextcloudError:
            continue
        rows.append({**item, "relative": relative, "is_dir": not item.get("content_type")})
    root_set = set(roots)
    if current in root_set:
        parent = ""
    else:
        candidate = "/".join(current.split("/")[:-1])
        try:
            parent = path_in_roots(client, candidate, roots)
        except NextcloudError:
            parent = ""
    return templates.TemplateResponse(request=request, name="genealogy_nextcloud_picker.html", context={"user": user, "handle": handle, "path": current, "parent": parent, "items": rows, "at_root": current in root_set})


@router.get("/genealogy/person/{handle}/picker/paperless", response_class=HTMLResponse)
def paperless_picker(handle: str, request: Request, q: str = Query(""), db: Session = Depends(get_db)):
    user = _writer(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    state = _paperless_state(db, user.family_id)
    if not state or not state.enabled:
        raise HTTPException(status_code=409, detail="Paperless-ngx ist nicht aktiviert")
    try:
        documents = _paperless_client(state).documents(q)
    except PaperlessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return templates.TemplateResponse(request=request, name="genealogy_paperless_picker.html", context={"user": user, "handle": handle, "q": q, "documents": documents})
