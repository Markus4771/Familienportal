from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.paperless import PaperlessClient
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin
from familienportal.secrets import read_secret, secret_is_available, validate_secret_reference

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _state(db: Session, family_id):
    return db.scalar(select(ConnectorState).where(ConnectorState.family_id == family_id, ConnectorState.connector_key == "paperless"))


def _client(state: ConnectorState) -> PaperlessClient:
    if not state.base_url or not state.secret_reference:
        raise HTTPException(status_code=409, detail="Paperless-ngx ist nicht vollständig konfiguriert")
    token = read_secret(state.secret_reference)
    if not token:
        raise HTTPException(status_code=409, detail="Das konfigurierte Paperless-Secret ist nicht verfügbar")
    return PaperlessClient(state.base_url, token)


@router.get("/platform/paperless", response_class=HTMLResponse)
def paperless_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    secret_available = bool(state and secret_is_available(state.secret_reference))
    return templates.TemplateResponse(request=request, name="paperless.html", context={"user": admin, "is_admin": True, "state": state, "secret_available": secret_available})


@router.post("/platform/paperless/config")
def save_config(request: Request, enabled: bool = Form(False), base_url: str = Form(""), secret_reference: str = Form("FAMILIENPORTAL_PAPERLESS_TOKEN"), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    try:
        secret_reference = validate_secret_reference(secret_reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _state(db, admin.family_id)
    if not state:
        state = ConnectorState(family_id=admin.family_id, connector_key="paperless")
        db.add(state)
    state.enabled = enabled
    state.base_url = base_url.strip().rstrip("/") or None
    state.secret_reference = secret_reference
    state.health_status = "configured" if enabled else "not_checked"
    state.health_message = None
    audit(db, "paperless.config.updated", actor=admin, target_type="connector", target_id="paperless")
    db.commit()
    return RedirectResponse("/platform/paperless?saved=1", status_code=303)


@router.post("/platform/paperless/health")
def health(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state:
        raise HTTPException(status_code=404, detail="Paperless-Connector nicht konfiguriert")
    result = _client(state).health()
    state.health_status = "ok" if result.healthy else "error"
    state.health_message = result.message
    state.health_checked_at = datetime.now(timezone.utc)
    audit(db, "paperless.health_checked", actor=admin, target_type="connector", target_id="paperless", details=state.health_status)
    db.commit()
    return RedirectResponse("/platform/paperless#health", status_code=303)
