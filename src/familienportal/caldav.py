from __future__ import annotations

import base64
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class CalDAVError(RuntimeError):
    pass


@dataclass(slots=True)
class CalDAVObject:
    href: str
    etag: str | None
    data: str


class CalDAVClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

    def _headers(self, content_type: str = "application/xml; charset=utf-8") -> dict[str, str]:
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {token}", "User-Agent": "Familienportal/0.5.2", "Content-Type": content_type}

    def _absolute_url(self, href: str) -> str:
        if href.startswith("http://") or href.startswith("https://"):
            return href
        return urljoin(f"{self.base_url}/", href.lstrip("/"))

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
        body = b'''<?xml version="1.0" encoding="utf-8" ?><d:propfind xmlns:d="DAV:"><d:prop><d:displayname/><d:resourcetype/></d:prop></d:propfind>'''
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

    def get_sync_token(self, calendar_href: str) -> str | None:
        body = b'''<?xml version="1.0" encoding="utf-8" ?><d:propfind xmlns:d="DAV:"><d:prop><d:sync-token/></d:prop></d:propfind>'''
        request = Request(self._absolute_url(calendar_href), method="PROPFIND", data=body, headers={**self._headers(), "Depth": "0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                xml = response.read()
        except HTTPError as exc:
            raise CalDAVError(f"Sync-Token HTTP {exc.code}") from exc
        ns = {"d": "DAV:"}
        root = ElementTree.fromstring(xml)
        return root.findtext(".//d:sync-token", default=None, namespaces=ns)

    def list_objects(self, calendar_href: str) -> list[CalDAVObject]:
        body = b'''<?xml version="1.0" encoding="utf-8" ?><c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav"><d:prop><d:getetag/><c:calendar-data/></d:prop><c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT"/></c:comp-filter></c:filter></c:calendar-query>'''
        request = Request(self._absolute_url(calendar_href), method="REPORT", data=body, headers={**self._headers(), "Depth": "1"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                xml = response.read()
        except HTTPError as exc:
            raise CalDAVError(f"Kalenderabfrage HTTP {exc.code}") from exc
        except URLError as exc:
            raise CalDAVError(f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc
        ns = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav"}
        root = ElementTree.fromstring(xml)
        items: list[CalDAVObject] = []
        for response in root.findall("d:response", ns):
            href = response.findtext("d:href", default="", namespaces=ns)
            etag = response.findtext("d:propstat/d:prop/d:getetag", default=None, namespaces=ns)
            data = response.findtext("d:propstat/d:prop/c:calendar-data", default="", namespaces=ns)
            if href and data:
                items.append(CalDAVObject(href=href, etag=etag, data=data))
        return items

    def get_object(self, href: str) -> CalDAVObject:
        request = Request(self._absolute_url(href), method="GET", headers=self._headers("text/calendar; charset=utf-8"))
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return CalDAVObject(href=href, etag=response.headers.get("ETag"), data=response.read().decode("utf-8"))
        except HTTPError as exc:
            raise CalDAVError(f"CalDAV GET HTTP {exc.code}") from exc
        except URLError as exc:
            raise CalDAVError(f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc

    def put_object(self, href: str, ics_data: str, etag: str | None = None) -> str | None:
        headers = self._headers("text/calendar; charset=utf-8")
        headers["If-Match" if etag else "If-None-Match"] = etag or "*"
        request = Request(self._absolute_url(href), method="PUT", data=ics_data.encode("utf-8"), headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.headers.get("ETag")
        except HTTPError as exc:
            if exc.code in {409, 412}:
                raise CalDAVError("Konflikt: Remote-Termin wurde zwischenzeitlich geändert.") from exc
            raise CalDAVError(f"CalDAV PUT HTTP {exc.code}") from exc
        except URLError as exc:
            raise CalDAVError(f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc

    def delete_object(self, href: str, etag: str | None = None) -> None:
        headers = self._headers()
        if etag:
            headers["If-Match"] = etag
        request = Request(self._absolute_url(href), method="DELETE", headers=headers)
        try:
            with urlopen(request, timeout=self.timeout):
                return
        except HTTPError as exc:
            if exc.code == 404:
                return
            if exc.code == 412:
                raise CalDAVError("Konflikt: Remote-Termin wurde vor dem Löschen geändert.") from exc
            raise CalDAVError(f"CalDAV DELETE HTTP {exc.code}") from exc
        except URLError as exc:
            raise CalDAVError(f"CalDAV-Verbindung fehlgeschlagen: {exc.reason}") from exc
