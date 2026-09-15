from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.database import get_db
from familienportal.models import Family, Household, Role, User
from familienportal.security import hash_password

router = APIRouter(tags=["setup"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def setup_required(db: Session) -> bool:
    return (db.scalar(select(func.count()).select_from(User)) or 0) == 0


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "familie"


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    if not setup_required(db):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("setup.html", {"request": request})


@router.post("/setup")
def setup_submit(
    family_name: str = Form(...),
    household_name: str = Form("Zuhause"),
    admin_name: str = Form(...),
    admin_email: str = Form(...),
    password: str = Form(...),
    profile: str = Form("small_family"),
    db: Session = Depends(get_db),
):
    if not setup_required(db):
        raise HTTPException(status_code=409, detail="Die Ersteinrichtung ist bereits abgeschlossen.")
    if profile not in {"small_family", "extended_family"}:
        raise HTTPException(status_code=400, detail="Ungültiges Familienprofil.")
    try:
        family = Family(name=family_name.strip(), slug=_slug(family_name), profile=profile)
        db.add(family)
        db.flush()
        household = Household(family_id=family.id, name=household_name.strip() or "Zuhause")
        db.add(household)
        db.flush()
        role = Role(family_id=family.id, name="Administrator", permissions="*", system_role=True)
        db.add(role)
        admin = User(
            family_id=family.id,
            household_id=household.id,
            email=admin_email.strip().lower(),
            display_name=admin_name.strip(),
            password_hash=hash_password(password),
            is_superadmin=True,
        )
        admin.roles.append(role)
        db.add(admin)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return RedirectResponse("/login?setup=complete", status_code=303)
