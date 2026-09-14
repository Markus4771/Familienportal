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

    def _request(self, path: str, method: str = "GET", payload: object | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            method=method,
            data=data,
            headers={
                "X-API-Key": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Familienportal/0.6.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise MailcowError(f"Mailcow API HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise MailcowError(f"Mailcow-Verbindung fehlgeschlagen: {exc.reason}") from exc
        except (ValueError, json.JSONDecodeError) as exc:
            raise MailcowError("Ungültige Mailcow-API-Antwort") from exc

    @staticmethod
    def _ensure_success(result: Any) -> Any:
        rows = result if isinstance(result, list) else [result]
        for row in rows:
            if isinstance(row, dict) and str(row.get("type", "success")) in {"danger", "error"}:
                raise MailcowError(str(row.get("msg") or "Mailcow API meldet einen Fehler"))
        return result

    def list_domains(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/domain/all")
        return data if isinstance(data, list) else []

    def list_mailboxes(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/mailbox/all")
        return data if isinstance(data, list) else []

    def get_mailbox(self, mailbox: str) -> dict[str, Any]:
        data = self._request(f"/api/v1/get/mailbox/{mailbox}")
        if not isinstance(data, dict):
            raise MailcowError("Postfach wurde nicht gefunden")
        return data

    def list_aliases(self) -> list[dict[str, Any]]:
        data = self._request("/api/v1/get/alias/all")
        return data if isinstance(data, list) else []

    def create_mailbox(self, *, address: str, name: str, password: str, quota_mb: int, force_password_update: bool = True) -> Any:
        local_part, separator, domain = address.partition("@")
        if not separator or not local_part or not domain:
            raise MailcowError("Ungültige E-Mail-Adresse")
        payload = {
            "active": "1",
            "domain": domain,
            "local_part": local_part,
            "name": name,
            "password": password,
            "password2": password,
            "quota": str(max(0, quota_mb)),
            "force_pw_update": "1" if force_password_update else "0",
            "tls_enforce_in": "1",
            "tls_enforce_out": "1",
        }
        return self._ensure_success(self._request("/api/v1/add/mailbox", "POST", payload))

    def edit_mailbox(self, mailbox: str, *, name: str | None = None, quota_mb: int | None = None, active: bool | None = None, password: str | None = None) -> Any:
        attr: dict[str, object] = {}
        if name is not None:
            attr["name"] = name
        if quota_mb is not None:
            attr["quota"] = str(max(0, quota_mb))
        if active is not None:
            attr["active"] = "1" if active else "0"
        if password:
            attr["password"] = password
            attr["password2"] = password
        if not attr:
            return None
        return self._ensure_success(self._request("/api/v1/edit/mailbox", "POST", {"items": [mailbox], "attr": attr}))

    def create_alias(self, address: str, destination: str, active: bool = True) -> Any:
        payload = {"address": address.strip(), "goto": destination.strip(), "active": "1" if active else "0"}
        return self._ensure_success(self._request("/api/v1/add/alias", "POST", payload))

    def edit_alias(self, alias_id: str, *, destination: str | None = None, active: bool | None = None) -> Any:
        attr: dict[str, object] = {}
        if destination is not None:
            attr["goto"] = destination.strip()
        if active is not None:
            attr["active"] = "1" if active else "0"
        if not attr:
            return None
        return self._ensure_success(self._request("/api/v1/edit/alias", "POST", {"items": [alias_id], "attr": attr}))

    def delete_alias(self, alias_id: str) -> Any:
        return self._ensure_success(self._request("/api/v1/delete/alias", "POST", [alias_id]))

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
