from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.gramps import GrampsClient, GrampsError
from familienportal.gramps_models import GrampsUserMapping
from familienportal.models import User
from familienportal.permissions import has_permission
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin
from familienportal.secrets import read_secret, secret_is_available, validate_secret_reference
from familienportal.web import _user_from_session

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _state(db: Session, family_id):
    return db.scalar(select(ConnectorState).where(ConnectorState.family_id == family_id, ConnectorState.connector_key == "gramps"))


def _client(state: ConnectorState) -> GrampsClient:
    if not state.base_url or not state.secret_reference:
        raise HTTPException(status_code=409, detail="Gramps Web ist nicht vollständig konfiguriert")
    value = read_secret(state.secret_reference)
    if not value:
        raise HTTPException(status_code=409, detail="Der konfigurierte Gramps-Web-Zugang ist nicht verfügbar")
    return GrampsClient(state.base_url, value)


@router.get("/genealogy", response_class=HTMLResponse)
def genealogy_page(request: Request, q: str = Query(""), db: Session = Depends(get_db)):
    user = _user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not has_permission(user, "genealogy.read"):
        raise HTTPException(status_code=403, detail="Berechtigung genealogy.read erforderlich")
    state = _state(db, user.family_id)
    results: list[dict] = []
    error = None
    if q.strip() and state and state.enabled:
        try:
            results = _client(state).search(q.strip(), "people")
        except (GrampsError, HTTPException) as exc:
            error = str(getattr(exc, "detail", exc))
    mapping = db.scalar(select(GrampsUserMapping).where(GrampsUserMapping.family_id == user.family_id, GrampsUserMapping.user_id == user.id))
    is_admin = user.is_superadmin or any(role.name == "Administrator" for role in user.roles)
    return templates.TemplateResponse(request=request, name="genealogy.html", context={"user": user, "is_admin": is_admin, "state": state, "query": q, "results": results, "mapping": mapping, "error": error})


@router.get("/platform/gramps", response_class=HTMLResponse)
def gramps_admin_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    users = db.scalars(select(User).where(User.family_id == admin.family_id).order_by(User.display_name)).unique().all()
    mappings = db.scalars(select(GrampsUserMapping).where(GrampsUserMapping.family_id == admin.family_id)).all()
    return templates.TemplateResponse(request=request, name="gramps_admin.html", context={"user": admin, "is_admin": True, "state": state, "secret_available": bool(state and secret_is_available(state.secret_reference)), "users": users, "mappings": mappings})


@router.post("/platform/gramps/config")
def save_gramps_config(request: Request, enabled: bool = Form(False), base_url: str = Form(""), secret_reference: str = Form("FAMILIENPORTAL_GRAMPS_ACCESS_TOKEN"), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    try:
        reference = validate_secret_reference(secret_reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _state(db, admin.family_id)
    if not state:
        state = ConnectorState(family_id=admin.family_id, connector_key="gramps")
        db.add(state)
    state.enabled = enabled
    state.base_url = base_url.strip().rstrip("/") or None
    state.secret_reference = reference
    state.health_status = "configured" if enabled else "not_checked"
    state.health_message = None
    audit(db, "gramps.config.updated", actor=admin, target_type="connector", target_id="gramps")
    db.commit()
    return RedirectResponse("/platform/gramps?saved=1", status_code=303)


@router.post("/platform/gramps/health")
def gramps_health(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state:
        raise HTTPException(status_code=404, detail="Gramps-Web-Connector nicht konfiguriert")
    try:
        result = _client(state).health()
        state.health_status = "ok" if result.healthy else "error"
        state.health_message = result.message
    except HTTPException as exc:
        state.health_status = "error"
        state.health_message = str(exc.detail)
    state.health_checked_at = datetime.now(timezone.utc)
    audit(db, "gramps.health_checked", actor=admin, target_type="connector", target_id="gramps", details=state.health_status)
    db.commit()
    return RedirectResponse("/platform/gramps#health", status_code=303)


@router.post("/platform/gramps/mapping")
def save_mapping(request: Request, user_id: UUID = Form(...), gramps_username: str = Form(""), gramps_role: str = Form("Guest"), person_handle: str = Form(""), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    target = db.get(User, user_id)
    if not target or target.family_id != admin.family_id:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    item = db.scalar(select(GrampsUserMapping).where(GrampsUserMapping.family_id == admin.family_id, GrampsUserMapping.user_id == user_id))
    if not item:
        item = GrampsUserMapping(family_id=admin.family_id, user_id=user_id)
        db.add(item)
    item.gramps_username = gramps_username.strip() or None
    item.gramps_role = gramps_role.strip() or "Guest"
    item.person_handle = person_handle.strip() or None
    item.updated_at = datetime.now(timezone.utc)
    audit(db, "gramps.mapping.updated", actor=admin, target_type="user", target_id=str(user_id))
    db.commit()
    return RedirectResponse("/platform/gramps#mappings", status_code=303)
