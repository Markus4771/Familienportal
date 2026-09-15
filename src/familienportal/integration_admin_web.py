from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.integration_admin import integration_overview, integration_summary
from familienportal.platform_web import _admin

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
