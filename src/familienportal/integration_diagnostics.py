from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class DiagnosticStep:
    key: str
    label: str
    status: str
    message: str


def diagnose_endpoint(base_url: str | None, *, enabled: bool, timeout: float = 5.0) -> list[DiagnosticStep]:
    steps: list[DiagnosticStep] = []
    if not enabled:
        return [DiagnosticStep("configuration", "Konfiguration", "disabled", "Connector ist deaktiviert.")]
    if not base_url:
        return [DiagnosticStep("configuration", "Konfiguration", "error", "Basis-URL fehlt.")]
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return [DiagnosticStep("configuration", "Konfiguration", "error", "Basis-URL ist ungültig oder enthält Zugangsdaten.")]
    steps.append(DiagnosticStep("configuration", "Konfiguration", "ok", "Basis-URL ist gültig."))
    request = Request(base_url, method="HEAD", headers={"User-Agent": "Familienportal/0.9.0"})
    try:
        with urlopen(request, timeout=max(1.0, min(float(timeout), 15.0))) as response:
            code = response.getcode()
        steps.append(DiagnosticStep("network", "Netzwerk", "ok", f"Dienst antwortet mit HTTP {code}."))
        steps.append(DiagnosticStep("authentication", "Authentifizierung", "unknown", "Dienstspezifische Anmeldung wird separat geprüft."))
    except HTTPError as exc:
        if exc.code in {401, 403}:
            steps.append(DiagnosticStep("network", "Netzwerk", "ok", f"Dienst erreichbar (HTTP {exc.code})."))
            steps.append(DiagnosticStep("authentication", "Authentifizierung", "unknown", "Basis-Endpunkt verlangt Anmeldung; Connector-Anmeldung wird separat geprüft."))
        elif exc.code in {405, 501}:
            steps.append(DiagnosticStep("network", "Netzwerk", "ok", f"Dienst erreichbar; HEAD wird nicht unterstützt (HTTP {exc.code})."))
            steps.append(DiagnosticStep("authentication", "Authentifizierung", "unknown", "Connector-Anmeldung wird separat geprüft."))
        elif 400 <= exc.code < 500:
            steps.append(DiagnosticStep("network", "Netzwerk", "ok", f"Dienst erreichbar (HTTP {exc.code})."))
            steps.append(DiagnosticStep("api", "API", "unknown", "Basis-Endpunkt liefert einen Clientfehler; dienstspezifische API wird separat geprüft."))
        else:
            steps.append(DiagnosticStep("network", "Netzwerk", "error", f"Dienst antwortet mit HTTP {exc.code}."))
    except (URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", None) or str(exc) or "Zeitüberschreitung oder Verbindungsfehler"
        steps.append(DiagnosticStep("network", "Netzwerk", "error", str(reason)))
    return steps
