from __future__ import annotations

import base64
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class CalDAVError(RuntimeError):
    pass


class CalDAVClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

    def _headers(self, content_type: str = "application/xml; charset=utf-8") -> dict[str, str]:
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "User-Agent": "Familienportal/0.5",
            "Content-Type": content_type,
        }

    def principal_url(self) -> str:
        return f"{self.base_url}/remote.php/dav/principals/users/{quote(self.username, safe='')}/"

    def calendar_home_url(self) -> str:
        return f"{self.base_url}/remote.php/dav/calendars/{quote(self.username, safe='')}/"

    def test(self) -> tuple[bool, str]:
        body = b'''<?xml version="1.0" encoding="utf-8" ?><d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>'''
        request = Request(self.principal_url(), method="PROPFIND", data=body, headers={**self._headers(), "Depth": "0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status in {200, 207}:
                    return True, f"CalDAV erreichbar (HTTP {response.status})."
                return False, f"CalDAV antwortet mit HTTP {response.status}."
        except HTTPError as exc:
            return False, f"CalDAV HTTP {exc.code}."
        except URLError as exc:
            return False, f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}"
        except TimeoutError:
            return False, "CalDAV-Zeitüberschreitung."

    def list_calendars(self) -> list[dict[str, str]]:
        body = b'''<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
  <d:prop><d:displayname/><d:resourcetype/></d:prop>
</d:propfind>'''
        request = Request(self.calendar_home_url(), method="PROPFIND", data=body, headers={**self._headers(), "Depth": "1"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                xml = response.read()
        except HTTPError as exc:
            raise CalDAVError(f"CalDAV HTTP {exc.code}") from exc
        except URLError as exc:
            raise CalDAVError(f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc
        ns = {"d": "DAV:"}
        root = ElementTree.fromstring(xml)
        items: list[dict[str, str]] = []
        for response in root.findall("d:response", ns):
            href = response.findtext("d:href", default="", namespaces=ns)
            name = response.findtext("d:propstat/d:prop/d:displayname", default="", namespaces=ns)
            if href.rstrip("/") == self.calendar_home_url().replace(self.base_url, "").rstrip("/"):
                continue
            if name:
                items.append({"name": name, "href": href})
        return items
