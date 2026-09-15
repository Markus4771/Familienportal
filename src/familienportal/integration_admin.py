from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.platform_models import ConnectorState


@dataclass(frozen=True, slots=True)
class IntegrationDefinition:
    key: str
    name: str
    category: str
    description: str
    admin_path: str


INTEGRATIONS: tuple[IntegrationDefinition, ...] = (
    IntegrationDefinition("nextcloud", "Nextcloud", "Cloud", "Dateien, Kalender und Freigaben", "/platform/nextcloud"),
    IntegrationDefinition("mailcow", "Mailcow", "Kommunikation", "E-Mail-Domains, Postfächer und Aliase", "/platform/mailcow"),
    IntegrationDefinition("gramps", "Gramps Web", "Familie", "Ahnenforschung, Personen und Familien", "/platform/gramps"),
    IntegrationDefinition("paperless", "Paperless-ngx", "Dokumente", "Dokumentenarchiv und Belege", "/platform/paperless"),
)


def definitions() -> tuple[IntegrationDefinition, ...]:
    return INTEGRATIONS


def integration_overview(db: Session, family_id: UUID) -> list[dict[str, object]]:
    states = {
        row.connector_key: row
        for row in db.scalars(select(ConnectorState).where(ConnectorState.family_id == family_id)).all()
    }
    result: list[dict[str, object]] = []
    for definition in INTEGRATIONS:
        state = states.get(definition.key)
        result.append(
            {
                "key": definition.key,
                "name": definition.name,
                "category": definition.category,
                "description": definition.description,
                "admin_path": definition.admin_path,
                "configured": bool(state and state.base_url),
                "enabled": bool(state and state.enabled),
                "health_status": state.health_status if state else "not_configured",
                "health_message": state.health_message if state else None,
                "health_checked_at": state.health_checked_at if state else None,
            }
        )
    return result


def integration_summary(rows: list[dict[str, object]]) -> dict[str, int]:
    total = len(rows)
    configured = sum(bool(row["configured"]) for row in rows)
    enabled = sum(bool(row["enabled"]) for row in rows)
    healthy = sum(row["health_status"] in {"healthy", "ok"} for row in rows)
    failing = sum(row["health_status"] in {"failed", "error", "unhealthy"} for row in rows)
    return {"total": total, "configured": configured, "enabled": enabled, "healthy": healthy, "failing": failing}


def safe_config(state: ConnectorState) -> dict[str, object]:
    try:
        raw = json.loads(state.config_json or "{}")
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    blocked = {"password", "token", "secret", "api_key", "apikey", "access_token"}
    return {key: value for key, value in raw.items() if key.lower() not in blocked}


def health_age_seconds(checked_at: datetime | None, now: datetime) -> int | None:
    if checked_at is None:
        return None
    if checked_at.tzinfo is None and now.tzinfo is not None:
        checked_at = checked_at.replace(tzinfo=now.tzinfo)
    return max(0, int((now - checked_at).total_seconds()))
