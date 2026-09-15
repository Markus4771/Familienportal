from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.integration_admin import integration_overview, integration_summary
from familienportal.platform_models import ConnectorState
from familienportal.platform_web import _admin, _probe_url

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/admin/integrations", response_class=HTMLResponse)
def integrations_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    rows = integration_overview(db, admin.family_id)
    return templates.TemplateResponse(
        request=request,
        name="integrations_admin.html",
        context={
            "user": admin,
            "is_admin": True,
            "integrations": rows,
            "summary": integration_summary(rows),
        },
    )


@router.post("/admin/integrations/health")
def check_all_integrations(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    states = db.scalars(select(ConnectorState).where(ConnectorState.family_id == admin.family_id)).all()
    checked = 0
    for state in states:
        if not state.enabled:
            state.health_status = "disabled"
            state.health_message = "Connector ist deaktiviert."
            continue
        if not state.base_url:
            state.health_status = "not_configured"
            state.health_message = "Basis-URL fehlt."
            continue
        state.health_status, state.health_message = _probe_url(state.base_url)
        state.health_checked_at = datetime.now(timezone.utc)
        checked += 1
    audit(
        db,
        "integrations.health_checked",
        actor=admin,
        target_type="family",
        target_id=str(admin.family_id),
        details=f"checked={checked}",
    )
    db.commit()
    return RedirectResponse("/admin/integrations?checked=1", status_code=303)
