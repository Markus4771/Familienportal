from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class MailcowError(RuntimeError):
    pass


@dataclass(slots=True)
class MailcowHealth:
    healthy: bool
    message: str
    domains: int = 0
    mailboxes: int = 0


class MailcowClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, path: str) -> Any:
        request = Request(f"{self.base_url}{path}", headers={"X-API-Key": self.api_key, "Accept": "application/json", "User-Agent": "Familienportal/0.6"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raise MailcowError(f"Mailcow API HTTP {exc.code}") from exc
        except URLError as exc:
            raise MailcowError(f"Mailcow-Verbindung fehlgeschlagen: {exc.reason}") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise MailcowError("Ungültige Mailcow-API-Antwort") from exc

    def list_domains(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/domain/all")
        return data if isinstance(data, list) else []

    def list_mailboxes(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/mailbox/all")
        return data if isinstance(data, list) else []

    def list_aliases(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/alias/all")
        return data if isinstance(data, list) else []

    def health(self) -> MailcowHealth:
        try:
            domains = self.list_domains()
            mailboxes = self.list_mailboxes()
            return MailcowHealth(True, "Mailcow API erreichbar und API-Key akzeptiert.", len(domains), len(mailboxes))
        except MailcowError as exc:
            return MailcowHealth(False, str(exc))

    def summary(self) -> dict[str, object]:
        domains = self.list_domains()
        mailboxes = self.list_mailboxes()
        aliases = self.list_aliases()
        quota_used = sum(int(item.get("quota_used", 0) or 0) for item in mailboxes)
        quota_limit = sum(int(item.get("quota", 0) or 0) for item in mailboxes)
        return {"domains": domains, "mailboxes": mailboxes, "aliases": aliases, "quota_used": quota_used, "quota_limit": quota_limit}
