from __future__ import annotations

from familienportal.gramps import GrampsClient
from familienportal.integration_diagnostics import DiagnosticStep, diagnose_endpoint
from familienportal.mailcow import MailcowClient
from familienportal.nextcloud import NextcloudClient
from familienportal.paperless import PaperlessClient
from familienportal.platform_models import ConnectorState
from familienportal.secrets import read_secret


def diagnose_connector(state: ConnectorState | None) -> list[DiagnosticStep]:
    if state is None:
        return [DiagnosticStep("configuration", "Konfiguration", "error", "Connector wurde noch nicht konfiguriert.")]
    generic = diagnose_endpoint(state.base_url, enabled=state.enabled)
    if not state.enabled or not state.base_url or generic[-1].status == "error":
        return generic
    secret = read_secret(state.secret_reference)
    if not secret:
        return generic + [DiagnosticStep("credentials", "Zugangsdaten", "error", "Das konfigurierte Secret ist nicht verfügbar.")]
    try:
        if state.connector_key == "nextcloud":
            if not state.username:
                return generic + [DiagnosticStep("credentials", "Zugangsdaten", "error", "Nextcloud-Benutzername fehlt.")]
            health = NextcloudClient(state.base_url, state.username, secret).health()
            return generic + [DiagnosticStep("api", "Nextcloud OCS/API", "ok" if health.healthy else "error", health.message)]
        if state.connector_key == "mailcow":
            health = MailcowClient(state.base_url, secret).health()
            message = health.message if not health.healthy else f"API-Key akzeptiert; {health.domains} Domains und {health.mailboxes} Postfächer sichtbar."
            return generic + [DiagnosticStep("api", "Mailcow API", "ok" if health.healthy else "error", message)]
        if state.connector_key == "gramps":
            health = GrampsClient(state.base_url, secret).health()
            return generic + [DiagnosticStep("api", "Gramps Web API", "ok" if health.healthy else "error", health.message)]
        if state.connector_key == "paperless":
            health = PaperlessClient(state.base_url, secret).health()
            return generic + [DiagnosticStep("api", "Paperless-ngx API", "ok" if health.healthy else "error", health.message)]
    except (ValueError, RuntimeError) as exc:
        return generic + [DiagnosticStep("api", "API", "error", str(exc))]
    return generic + [DiagnosticStep("api", "API", "unknown", "Für diesen Connector ist noch keine dienstspezifische Prüfung vorhanden.")]
