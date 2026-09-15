from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.integration_admin import definitions, integration_overview, integration_summary
from familienportal.integration_service_diagnostics import diagnose_connector
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


def _result(steps):
    errors = [step for step in steps if step.status == "error"]
    warnings = [step for step in steps if step.status == "warning"]
    if errors:
        return "error", errors[-1].message
    if warnings:
        return "degraded", warnings[-1].message
    if steps and all(step.status in {"ok", "unknown"} for step in steps):
        return "healthy", "Integration erfolgreich geprüft."
    if steps and steps[0].status == "disabled":
        return "disabled", steps[0].message
    return "not_checked", "Integration konnte nicht vollständig geprüft werden."


@router.get("/admin/integrations", response_class=HTMLResponse)
def integrations_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    rows = integration_overview(db, admin.family_id)
    return templates.TemplateResponse(request=request, name="integrations_admin.html", context={"user": admin, "is_admin": True, "integrations": rows, "summary": integration_summary(rows)})


@router.get("/admin/integrations/{connector_key}/diagnostics", response_class=HTMLResponse)
def integration_diagnostics(connector_key: str, request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    definition = next((item for item in definitions() if item.key == connector_key), None)
    if definition is None:
        raise HTTPException(status_code=404, detail="Integration nicht gefunden")
    state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == admin.family_id, ConnectorState.connector_key == connector_key))
    steps = diagnose_connector(state)
    return templates.TemplateResponse(request=request, name="integration_diagnostics.html", context={"user": admin, "is_admin": True, "integration": definition, "state": state, "steps": steps})


@router.post("/admin/integrations/health")
def check_all_integrations(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    states = db.scalars(select(ConnectorState).where(ConnectorState.family_id == admin.family_id)).all()
    checked = 0
    for state in states:
        steps = diagnose_connector(state)
        state.health_status, state.health_message = _result(steps)
        state.health_checked_at = datetime.now(timezone.utc)
        if state.enabled:
            checked += 1
    audit(db, "integrations.health_checked", actor=admin, target_type="family", target_id=str(admin.family_id), details=f"checked={checked}")
    db.commit()
    return RedirectResponse("/admin/integrations?checked=1", status_code=303)
