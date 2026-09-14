from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class NextcloudError(RuntimeError):
    pass


@dataclass(slots=True)
class NextcloudHealth:
    healthy: bool
    message: str
    version: str | None = None
    product: str | None = None


class NextcloudClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

    def _headers(self, *, ocs: bool = False, content_type: str | None = None) -> dict[str, str]:
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        headers = {"Authorization": f"Basic {token}", "User-Agent": "Familienportal/0.4.1"}
        if ocs:
            headers["OCS-APIRequest"] = "true"
            headers["Accept"] = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _request(self, method: str, path: str, *, data: bytes | None = None, ocs: bool = False) -> tuple[int, bytes, dict[str, str]]:
        request = Request(f"{self.base_url}{path}", method=method, data=data, headers=self._headers(ocs=ocs))
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.status, response.read(), dict(response.headers.items())
        except HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise NextcloudError(f"HTTP {exc.code}: {body[:300]}") from exc
        except URLError as exc:
            raise NextcloudError(f"Verbindung fehlgeschlagen: {exc.reason}") from exc
        except TimeoutError as exc:
            raise NextcloudError("Zeitüberschreitung bei Nextcloud.") from exc

    def _ocs_get(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        _, body, _ = self._request("GET", f"{path}{query}", ocs=True)
        try:
            payload = json.loads(body.decode())
            meta = payload.get("ocs", {}).get("meta", {})
            if int(meta.get("statuscode", 100)) != 100:
                raise NextcloudError(str(meta.get("message") or "OCS-Fehler"))
            return payload.get("ocs", {}).get("data")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise NextcloudError("Ungültige OCS-Antwort von Nextcloud.") from exc

    def health(self) -> NextcloudHealth:
        try:
            _, body, _ = self._request("GET", "/status.php")
            status = json.loads(body.decode())
            if not status.get("installed"):
                return NextcloudHealth(False, "Nextcloud ist nicht vollständig installiert.")
            if status.get("maintenance"):
                return NextcloudHealth(False, "Nextcloud befindet sich im Wartungsmodus.", status.get("version"), status.get("productname"))
            user = self.current_user()
            label = user.get("display-name") or user.get("id") or self.username
            return NextcloudHealth(True, f"Nextcloud erreichbar; Anmeldung als {label} erfolgreich.", status.get("version"), status.get("productname"))
        except (NextcloudError, ValueError, json.JSONDecodeError) as exc:
            return NextcloudHealth(False, str(exc))

    def current_user(self) -> dict[str, Any]:
        data = self._ocs_get("/ocs/v2.php/cloud/user")
        return data if isinstance(data, dict) else {}

    def list_users(self, limit: int = 100) -> list[str]:
        data = self._ocs_get("/ocs/v1.php/cloud/users", {"limit": str(limit)})
        users = data.get("users", []) if isinstance(data, dict) else []
        return [str(item) for item in users]

    def list_groups(self, limit: int = 100) -> list[str]:
        data = self._ocs_get("/ocs/v1.php/cloud/groups", {"limit": str(limit)})
        groups = data.get("groups", []) if isinstance(data, dict) else []
        return [str(item) for item in groups]

    def list_shares(self, limit: int = 100) -> list[dict[str, Any]]:
        data = self._ocs_get("/ocs/v2.php/apps/files_sharing/api/v1/shares", {"format": "json", "limit": str(limit)})
        return data if isinstance(data, list) else []

    def dav_endpoints(self) -> dict[str, str]:
        user = quote(self.username, safe="")
        return {
            "webdav": f"{self.base_url}/remote.php/dav/files/{user}/",
            "caldav": f"{self.base_url}/remote.php/dav/calendars/{user}/",
            "carddav": f"{self.base_url}/remote.php/dav/addressbooks/users/{user}/",
        }

    def _dav_path(self, relative_path: str = "") -> str:
        user = quote(self.username, safe="")
        path = relative_path.strip("/")
        suffix = f"/{quote(path, safe='/')}" if path else ""
        return f"/remote.php/dav/files/{user}{suffix}/"

    def list_files(self, relative_path: str = "", depth: int = 1) -> list[dict[str, str | None]]:
        body = b'<?xml version="1.0" encoding="utf-8" ?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/><d:getcontentlength/><d:getcontenttype/><d:getlastmodified/></d:prop></d:propfind>'
        request = Request(
            f"{self.base_url}{self._dav_path(relative_path)}",
            method="PROPFIND",
            data=body,
            headers={**self._headers(content_type="application/xml; charset=utf-8"), "Depth": str(depth)},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                xml = response.read()
        except HTTPError as exc:
            raise NextcloudError(f"WebDAV HTTP {exc.code}") from exc
        except URLError as exc:
            raise NextcloudError(f"WebDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc
        ns = {"d": "DAV:"}
        root = ElementTree.fromstring(xml)
        items: list[dict[str, str | None]] = []
        for response in root.findall("d:response", ns):
            href = response.findtext("d:href", default="", namespaces=ns)
            prop = response.find("d:propstat/d:prop", ns)
            if prop is None:
                continue
            items.append({
                "href": href,
                "name": prop.findtext("d:displayname", default="", namespaces=ns),
                "size": prop.findtext("d:getcontentlength", default=None, namespaces=ns),
                "content_type": prop.findtext("d:getcontenttype", default=None, namespaces=ns),
                "modified": prop.findtext("d:getlastmodified", default=None, namespaces=ns),
            })
        return items

    def create_folder(self, relative_path: str) -> None:
        path = relative_path.strip("/")
        if not path or any(part in {".", ".."} for part in path.split("/")):
            raise NextcloudError("Ungültiger Ordnerpfad.")
        request = Request(f"{self.base_url}{self._dav_path(path)}", method="MKCOL", headers=self._headers())
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status not in {201, 405}:
                    raise NextcloudError(f"WebDAV MKCOL HTTP {response.status}")
        except HTTPError as exc:
            if exc.code != 405:
                raise NextcloudError(f"WebDAV MKCOL HTTP {exc.code}") from exc
        except URLError as exc:
            raise NextcloudError(f"WebDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc

    def diagnostics(self) -> dict[str, str]:
        results: dict[str, str] = {}
        health = self.health()
        results["ocs"] = "ok" if health.healthy else health.message
        try:
            self.list_files(depth=0)
            results["webdav"] = "ok"
        except NextcloudError as exc:
            results["webdav"] = str(exc)
        for name, url in self.dav_endpoints().items():
            if name != "webdav":
                results[name] = url
        return results
