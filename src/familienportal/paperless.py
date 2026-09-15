from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PaperlessError(RuntimeError):
    pass


@dataclass(slots=True)
class PaperlessHealth:
    healthy: bool
    message: str


class PaperlessClient:
    def __init__(self, base_url: str, token: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        req = Request(f"{self.base_url}{path}{query}", headers={"Authorization": f"Token {self.token}", "Accept": "application/json", "User-Agent": "Familienportal/0.8.5"})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raise PaperlessError(f"Paperless HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise PaperlessError(f"Paperless-Verbindung fehlgeschlagen: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise PaperlessError("Ungültige Paperless-Antwort") from exc

    def health(self) -> PaperlessHealth:
        try:
            self.documents(page_size=1)
            return PaperlessHealth(True, "Paperless-ngx erreichbar")
        except PaperlessError as exc:
            return PaperlessHealth(False, str(exc))

    def documents(self, query: str = "", page_size: int = 50) -> list[dict[str, Any]]:
        params = {"page_size": str(page_size), "ordering": "-created"}
        if query.strip():
            params["query"] = query.strip()
        payload = self._get("/api/documents/", params)
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        return [item for item in rows if isinstance(item, dict)]
