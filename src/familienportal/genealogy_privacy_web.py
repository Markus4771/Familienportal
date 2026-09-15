from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.api import audit
from familienportal.database import get_db
from familienportal.platform_models import FamilySetting
from familienportal.platform_web import _admin

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="src/familienportal/templates")
KEY_MODE = "genealogy.privacy.living_mode"
KEY_AGE = "genealogy.privacy.living_age_years"


def _get(db: Session, family_id, key: str, default: str) -> str:
    row = db.scalar(select(FamilySetting).where(FamilySetting.family_id == family_id, FamilySetting.setting_key == key))
    return row.value if row else default


def _set(db: Session, family_id, key: str, value: str) -> None:
    row = db.scalar(select(FamilySetting).where(FamilySetting.family_id == family_id, FamilySetting.setting_key == key))
    if not row:
        row = FamilySetting(family_id=family_id, setting_key=key, value=value)
        db.add(row)
    else:
        row.value = value


@router.get("/genealogy/privacy", response_class=HTMLResponse)
def privacy_page(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    return templates.TemplateResponse(request=request, name="genealogy_privacy.html", context={"user": admin, "is_admin": True, "mode": _get(db, admin.family_id, KEY_MODE, "redact"), "age": _get(db, admin.family_id, KEY_AGE, "110")})


@router.post("/genealogy/privacy")
def save_privacy(request: Request, living_mode: str = Form("redact"), living_age_years: int = Form(110), db: Session = Depends(get_db)):
    admin = _admin(request, db)
    if living_mode not in {"redact", "hide"}:
        living_mode = "redact"
    living_age_years = min(130, max(80, living_age_years))
    _set(db, admin.family_id, KEY_MODE, living_mode)
    _set(db, admin.family_id, KEY_AGE, str(living_age_years))
    audit(db, "genealogy.privacy.updated", actor=admin, target_type="family", target_id=str(admin.family_id), details=f"mode={living_mode}, age={living_age_years}")
    db.commit()
    return RedirectResponse("/genealogy/privacy?saved=1", status_code=303)
