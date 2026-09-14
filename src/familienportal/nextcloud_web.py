from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.nextcloud import NextcloudClient, NextcloudError
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin
from familienportal.secrets import read_secret, secret_is_available, validate_secret_reference

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _state(db: Session, family_id):
    return db.scalar(
        select(ConnectorState).where(
            ConnectorState.family_id == family_id,
            ConnectorState.connector_key == "nextcloud",
        )
    )


def _client(state: ConnectorState) -> NextcloudClient:
    if not state.base_url or not state.username or not state.secret_reference:
        raise HTTPException(status_code=409, detail="Nextcloud ist nicht vollständig konfiguriert")
    password = read_secret(state.secret_reference)
    if not password:
        raise HTTPException(status_code=409, detail="Das konfigurierte Nextcloud-Secret ist nicht verfügbar")
    return NextcloudClient(state.base_url, state.username, password)


@router.get("/platform/nextcloud", response_class=HTMLResponse)
def nextcloud_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    users: list[str] = []
    groups: list[str] = []
    files: list[dict[str, object]] = []
    shares: list[dict[str, object]] = []
    endpoints: dict[str, str] = {}
    live_error: str | None = None
    secret_available = bool(state and secret_is_available(state.secret_reference))
    if state and state.enabled and state.base_url and state.username and secret_available:
        client = _client(state)
        try:
            users = client.list_users()
            groups = client.list_groups()
            files = client.list_files()
            shares = client.list_shares()
            endpoints = client.dav_endpoints()
        except NextcloudError as exc:
            live_error = str(exc)
    return templates.TemplateResponse(
        request=request,
        name="nextcloud.html",
        context={
            "user": admin,
            "is_admin": True,
            "state": state,
            "secret_available": secret_available,
            "users": users,
            "groups": groups,
            "files": files,
            "shares": shares,
            "endpoints": endpoints,
            "live_error": live_error,
        },
    )


@router.post("/platform/nextcloud/config")
def save_nextcloud_config(
    request: Request,
    enabled: bool = Form(False),
    base_url: str = Form(""),
    username: str = Form(""),
    secret_reference: str = Form("FAMILIENPORTAL_NEXTCLOUD_APP_PASSWORD"),
    db: Session = Depends(get_db),
):
    admin = _admin(request, db)
    try:
        secret_reference = validate_secret_reference(secret_reference)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    state = _state(db, admin.family_id)
    if not state:
        state = ConnectorState(family_id=admin.family_id, connector_key="nextcloud")
        db.add(state)
    state.enabled = enabled
    state.base_url = base_url.strip().rstrip("/") or None
    state.username = username.strip() or None
    state.secret_reference = secret_reference
    state.health_status = "configured" if enabled else "not_checked"
    state.health_message = None
    audit(db, "nextcloud.config.updated", actor=admin, target_type="connector", target_id="nextcloud")
    db.commit()
    return RedirectResponse("/platform/nextcloud?saved=1", status_code=303)


@router.post("/platform/nextcloud/health")
def nextcloud_health(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    state = _state(db, admin.family_id)
    if not state:
        raise HTTPException(status_code=404, detail="Nextcloud-Connector nicht konfiguriert")
    try:
        result = _client(state).health()
        state.health_status = "ok" if result.healthy else "error"
        state.health_message = result.message
        if result.version:
            state.config_json = '{"version":"' + result.version.replace('"', '') + '"}'
    except HTTPException as exc:
        state.health_status = "error"
        state.health_message = str(exc.detail)
    state.health_checked_at = datetime.now(timezone.utc)
    audit(db, "nextcloud.health_checked", actor=admin, target_type="connector", target_id="nextcloud", details=state.health_status)
    db.commit()
    return RedirectResponse("/platform/nextcloud#health", status_code=303)
