from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from familienportal import __version__
from familienportal.config import get_settings
from familienportal.integration_admin import integration_overview, integration_summary
from familienportal.models import AuditEvent, Household, User
from familienportal.platform_models import ModuleState


def _storage(path: str) -> dict[str, object]:
    target = Path(path)
    probe = target if target.exists() else Path("/")
    usage = shutil.disk_usage(probe)
    return {"path": path, "exists": target.exists(), "free_gb": round(usage.free / 1024**3, 1), "total_gb": round(usage.total / 1024**3, 1), "used_percent": round(usage.used * 100 / usage.total, 1)}


def admin_status(db: Session, family_id: UUID) -> dict[str, object]:
    settings = get_settings()
    integrations = integration_overview(db, family_id)
    summary = integration_summary(integrations)
    users = db.scalar(select(func.count()).select_from(User).where(User.family_id == family_id)) or 0
    households = db.scalar(select(func.count()).select_from(Household).where(Household.family_id == family_id)) or 0
    enabled_modules = db.scalar(select(func.count()).select_from(ModuleState).where(ModuleState.family_id == family_id, ModuleState.enabled.is_(True))) or 0
    recent_audit = db.scalars(select(AuditEvent).where(AuditEvent.family_id == family_id).order_by(AuditEvent.created_at.desc()).limit(10)).all()
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        database = exc.__class__.__name__
    migration = "unknown"
    try:
        migration = str(db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none() or "none")
    except Exception:
        migration = "unavailable"
    storage = [_storage("/opt/familienportal"), _storage("/var/lib/familienportal"), _storage("/var/backups/familienportal")]
    health = "ok"
    if summary["failing"] or database != "ok" or any(item["used_percent"] >= 90 for item in storage):
        health = "warning"
    return {"health": health, "version": __version__, "environment": settings.environment, "database": database, "database_backend": settings.database_backend, "migration": migration, "users": users, "households": households, "enabled_modules": enabled_modules, "integrations": integrations, "integration_summary": summary, "storage": storage, "recent_audit": recent_audit}
