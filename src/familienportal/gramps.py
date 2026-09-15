from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GrampsError(RuntimeError):
    pass


@dataclass(slots=True)
class GrampsHealth:
    healthy: bool
    message: str


class GrampsClient:
    def __init__(self, base_url: str, access_token: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        request = Request(f"{self.base_url}{path}", headers={"Accept": "application/json", "Authorization": f"Bearer {self.access_token}", "User-Agent": "Familienportal/0.8.7"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise GrampsError(f"Gramps Web API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise GrampsError(f"Gramps-Web-Verbindung fehlgeschlagen: {exc.reason}") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise GrampsError("Ungültige Gramps-Web-API-Antwort") from exc

    @staticmethod
    def _rows(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for key in ("data", "results", "items"):
                rows = value.get(key)
                if isinstance(rows, list):
                    return [item for item in rows if isinstance(item, dict)]
        return []

    def people(self, page: int = 1, pagesize: int = 50) -> list[dict[str, Any]]:
        params = urlencode({"page": max(1, page), "pagesize": min(max(1, pagesize), 200), "profile": "self,families"})
        return self._rows(self._request(f"/api/people/?{params}"))

    def families(self, page: int = 1, pagesize: int = 50) -> list[dict[str, Any]]:
        params = urlencode({"page": max(1, page), "pagesize": min(max(1, pagesize), 200), "profile": "self"})
        return self._rows(self._request(f"/api/families/?{params}"))

    def _all_pages(self, loader, *, pagesize: int = 200, max_pages: int = 100) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for page in range(1, max_pages + 1):
            rows = loader(page=page, pagesize=pagesize)
            if not rows:
                break
            new_rows = []
            for item in rows:
                identity = str(item.get("handle") or item.get("gramps_id") or repr(item))
                if identity not in seen:
                    seen.add(identity)
                    new_rows.append(item)
            result.extend(new_rows)
            if len(rows) < pagesize or not new_rows:
                break
        return result

    def all_people(self, *, max_pages: int = 100) -> list[dict[str, Any]]:
        return self._all_pages(self.people, max_pages=max_pages)

    def all_families(self, *, max_pages: int = 100) -> list[dict[str, Any]]:
        return self._all_pages(self.families, max_pages=max_pages)

    def person(self, handle: str) -> dict[str, Any]:
        result = self._request(f"/api/people/{quote(handle, safe='')}")
        if not isinstance(result, dict):
            raise GrampsError("Person wurde nicht gefunden")
        return result

    def family(self, handle: str) -> dict[str, Any]:
        result = self._request(f"/api/families/{quote(handle, safe='')}")
        if not isinstance(result, dict):
            raise GrampsError("Familie wurde nicht gefunden")
        return result

    def media(self, handle: str) -> dict[str, Any]:
        result = self._request(f"/api/media/{quote(handle, safe='')}")
        if not isinstance(result, dict):
            raise GrampsError("Medium wurde nicht gefunden")
        return result

    def search(self, query_text: str, object_type: str = "people") -> list[dict[str, Any]]:
        query_text = query_text.strip()
        if not query_text:
            return []
        params = urlencode({"query": query_text, "type": object_type})
        return self._rows(self._request(f"/api/search/?{params}"))

    def health(self) -> GrampsHealth:
        try:
            self.people(pagesize=1)
            return GrampsHealth(True, "Gramps Web API erreichbar und Token akzeptiert.")
        except GrampsError as exc:
            return GrampsHealth(False, str(exc))
