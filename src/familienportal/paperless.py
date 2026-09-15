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


@dataclass(slots=True)
class PaperlessBinary:
    content: bytes
    content_type: str
    filename: str | None = None


class PaperlessClient:
    def __init__(self, base_url: str, token: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(self, path: str, accept: str = "application/json"):
        req = Request(f"{self.base_url}{path}", headers={"Authorization": f"Token {self.token}", "Accept": accept, "User-Agent": "Familienportal/0.8.5"})
        try:
            return urlopen(req, timeout=self.timeout)
        except HTTPError as exc:
            raise PaperlessError(f"Paperless HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise PaperlessError(f"Paperless-Verbindung fehlgeschlagen: {exc}") from exc

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        try:
            with self._request(f"{path}{query}") as response:
                return json.loads(response.read().decode())
        except json.JSONDecodeError as exc:
            raise PaperlessError("Ungültige Paperless-Antwort") from exc

    def _binary(self, path: str, accept: str) -> PaperlessBinary:
        with self._request(path, accept) as response:
            content_type = response.headers.get_content_type() or "application/octet-stream"
            disposition = response.headers.get("Content-Disposition", "")
            filename = None
            if "filename=" in disposition:
                filename = disposition.split("filename=", 1)[1].strip().strip('"')
            return PaperlessBinary(response.read(), content_type, filename)

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

    def document(self, document_id: int) -> dict[str, Any]:
        payload = self._get(f"/api/documents/{document_id}/")
        return payload if isinstance(payload, dict) else {}

    def preview(self, document_id: int) -> PaperlessBinary:
        return self._binary(f"/api/documents/{document_id}/preview/", "image/*")

    def download(self, document_id: int) -> PaperlessBinary:
        return self._binary(f"/api/documents/{document_id}/download/", "application/pdf,application/octet-stream,*/*")
