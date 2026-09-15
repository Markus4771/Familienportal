from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from familienportal.admin_status import admin_status
from familienportal.database import get_db
from familienportal.platform_web import _admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/system/status")
def system_status_api(request: Request, db: Session = Depends(get_db)):
    admin = _admin(request, db)
    status = admin_status(db, admin.family_id)
    return {
        "health": status["health"],
        "users": status["users"],
        "households": status["households"],
        "enabled_modules": status["enabled_modules"],
        "integrations": [
            {
                "key": item["key"],
                "configured": item["configured"],
                "enabled": item["enabled"],
                "health_status": item["health_status"],
                "health_message": item["health_message"],
                "health_checked_at": item["health_checked_at"],
            }
            for item in status["integrations"]
        ],
        "integration_summary": status["integration_summary"],
    }
