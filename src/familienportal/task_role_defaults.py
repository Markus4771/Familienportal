from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.models import Role

TASK_ROLE_DEFAULTS: dict[str, set[str]] = {
    "Administrator": {"*"},
    "Erwachsene": {"tasks.read", "tasks.create", "tasks.edit", "tasks.assign", "tasks.complete", "tasks.delete", "tasks.manage"},
    "Kind": {"tasks.read", "tasks.create", "tasks.edit", "tasks.complete"},
    "Gast": {"tasks.read"},
}


def apply_task_role_defaults(db: Session, family_id) -> int:
    """Add missing 0.10 task permissions without deleting custom permissions."""
    changed = 0
    roles = db.scalars(select(Role).where(Role.family_id == family_id)).all()
    for role in roles:
        defaults = TASK_ROLE_DEFAULTS.get(role.name)
        if not defaults:
            continue
        current = {item.strip() for item in role.permissions.split(",") if item.strip()}
        if "*" in current:
            continue
        merged = current | defaults
        if merged != current:
            role.permissions = ",".join(sorted(merged))
            changed += 1
    if changed:
        db.commit()
    return changed
