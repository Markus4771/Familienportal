from __future__ import annotations

import json

from sqlalchemy.orm import Session

from familienportal.models import AuditEvent, User
from familienportal.task_models import FamilyTask


def audit_task(db: Session, action: str, actor: User, task: FamilyTask, **details: object) -> AuditEvent:
    """Record task lifecycle changes without storing private task content."""
    safe_details = {
        "status": task.status,
        "priority": task.priority,
        "assignee_user_id": str(task.assignee_user_id) if task.assignee_user_id else None,
        "household_id": str(task.household_id) if task.household_id else None,
        "is_private": bool(task.is_private),
        **details,
    }
    event = AuditEvent(
        family_id=actor.family_id,
        actor_user_id=actor.id,
        action=action,
        target_type="family_task",
        target_id=str(task.id),
        details=json.dumps(safe_details, ensure_ascii=False, default=str),
    )
    db.add(event)
    return event
