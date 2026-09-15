from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.integration_admin import integration_overview, integration_summary
from familienportal.models import AuditEvent, Household, User
from familienportal.platform_models import ModuleState


def admin_status(db: Session, family_id: UUID) -> dict[str, object]:
    integrations = integration_overview(db, family_id)
    summary = integration_summary(integrations)
    users = db.scalar(select(func.count()).select_from(User).where(User.family_id == family_id)) or 0
    households = db.scalar(select(func.count()).select_from(Household).where(Household.family_id == family_id)) or 0
    enabled_modules = db.scalar(select(func.count()).select_from(ModuleState).where(ModuleState.family_id == family_id, ModuleState.enabled.is_(True))) or 0
    recent_audit = db.scalars(select(AuditEvent).where(AuditEvent.family_id == family_id).order_by(AuditEvent.created_at.desc()).limit(10)).all()
    health = "ok"
    if summary["failing"]:
        health = "warning"
    return {
        "health": health,
        "users": users,
        "households": households,
        "enabled_modules": enabled_modules,
        "integrations": integrations,
        "integration_summary": summary,
        "recent_audit": recent_audit,
    }
