from __future__ import annotations

from familienportal.gramps import GrampsClient
from familienportal.integration_diagnostics import DiagnosticStep, diagnose_endpoint
from familienportal.mailcow import MailcowClient
from familienportal.nextcloud import NextcloudClient
from familienportal.paperless import PaperlessClient
from familienportal.platform_models import ConnectorState
from familienportal.secrets import read_secret


def _has_error(steps: list[DiagnosticStep]) -> bool:
    return any(step.status == "error" for step in steps)


def _api_step(label: str, healthy: bool, message: str) -> DiagnosticStep:
    return DiagnosticStep("api", label, "ok" if healthy else "error", message[:500])


def diagnose_connector(state: ConnectorState | None) -> list[DiagnosticStep]:
    if state is None:
        return [DiagnosticStep("configuration", "Konfiguration", "error", "Connector wurde noch nicht konfiguriert.")]
    generic = diagnose_endpoint(state.base_url, enabled=state.enabled)
    if not state.enabled or not state.base_url or _has_error(generic):
        return generic
    try:
        secret = read_secret(state.secret_reference)
    except (ValueError, RuntimeError) as exc:
        return generic + [DiagnosticStep("credentials", "Zugangsdaten", "error", f"Secret-Konfiguration ungültig: {str(exc)[:300]}")]
    if not secret:
        return generic + [DiagnosticStep("credentials", "Zugangsdaten", "error", "Das konfigurierte Secret ist nicht verfügbar.")]
    steps = generic + [DiagnosticStep("credentials", "Zugangsdaten", "ok", "Secret-Referenz ist verfügbar.")]
    try:
        if state.connector_key == "nextcloud":
            if not state.username:
                return generic + [DiagnosticStep("credentials", "Zugangsdaten", "error", "Nextcloud-Benutzername fehlt.")]
            health = NextcloudClient(state.base_url, state.username, secret).health()
            return steps + [_api_step("Nextcloud OCS/API", health.healthy, health.message)]
        if state.connector_key == "mailcow":
            health = MailcowClient(state.base_url, secret).health()
            message = health.message if not health.healthy else f"API-Key akzeptiert; {health.domains} Domains und {health.mailboxes} Postfächer sichtbar."
            return steps + [_api_step("Mailcow API", health.healthy, message)]
        if state.connector_key == "gramps":
            health = GrampsClient(state.base_url, secret).health()
            return steps + [_api_step("Gramps Web API", health.healthy, health.message)]
        if state.connector_key == "paperless":
            health = PaperlessClient(state.base_url, secret).health()
            return steps + [_api_step("Paperless-ngx API", health.healthy, health.message)]
    except (ValueError, RuntimeError, OSError) as exc:
        return steps + [DiagnosticStep("api", "API", "error", str(exc)[:500])]
    return steps + [DiagnosticStep("api", "API", "unknown", "Für diesen Connector ist noch keine dienstspezifische Prüfung vorhanden.")]
