from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from familienportal.admin_status import admin_status
from familienportal.database import get_db
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")


@router.get("/admin/system", response_class=HTMLResponse)
def system_status(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    status = admin_status(db, admin.family_id)
    return templates.TemplateResponse(request=request, name="admin_system.html", context={"user": admin, "is_admin": True, "status": status})
