from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.extensions import BUILTIN_CONNECTORS, BUILTIN_MODULES
from familienportal.permissions import has_permission
from familienportal.platform_models import ConnectorState, FamilySetting, ModuleState
from familienportal.models import User


def enabled_modules(db: Session, family_id: UUID, user: User | None = None) -> list[dict[str, object]]:
    states = {
        item.module_key: item
        for item in db.scalars(select(ModuleState).where(ModuleState.family_id == family_id)).all()
    }
    result: list[dict[str, object]] = []
    for key, definition in BUILTIN_MODULES.items():
        state = states.get(key)
        enabled = state.enabled if state else bool(definition.get("default", False))
        if not enabled:
            continue
        permission = str(definition.get("permission", f"{key}.read"))
        if user is not None and not has_permission(user, permission):
            continue
        result.append({"key": key, **definition, "enabled": True})
    return result


def configured_connectors(db: Session, family_id: UUID) -> list[dict[str, object]]:
    states = {
        item.connector_key: item
        for item in db.scalars(select(ConnectorState).where(ConnectorState.family_id == family_id)).all()
    }
    result: list[dict[str, object]] = []
    for key, definition in BUILTIN_CONNECTORS.items():
        state = states.get(key)
        if not state or not state.enabled:
            continue
        result.append(
            {
                "key": key,
                **definition,
                "enabled": True,
                "base_url": state.base_url,
                "health_status": state.health_status,
                "health_message": state.health_message,
            }
        )
    return result


def family_settings(db: Session, family_id: UUID) -> dict[str, str]:
    return {
        item.setting_key: item.value
        for item in db.scalars(select(FamilySetting).where(FamilySetting.family_id == family_id)).all()
    }
