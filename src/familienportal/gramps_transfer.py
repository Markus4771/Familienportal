from __future__ import annotations

import json
import re
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from familienportal.gramps import GrampsClient, GrampsError

_TASK_ID = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
_PROCESSED_PREFIX = "/api/exporters/ged/file/processed/"


def _call(client: GrampsClient, path: str, *, method: str = "GET", data: bytes | None = None, content_type: str | None = None) -> Any:
    if not path.startswith("/api/") or "://" in path or "\r" in path or "\n" in path:
        raise GrampsError("Ungültiger Gramps-Web-API-Pfad")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {client.access_token}", "User-Agent": "Familienportal/0.8.7"}
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(f"{client.base_url}{path}", method=method, data=data, headers=headers)
    try:
        with urlopen(request, timeout=client.timeout) as response:
            raw = response.read()
            if "application/json" in (response.headers.get("Content-Type") or ""):
                try:
                    return json.loads(raw.decode("utf-8")) if raw else None
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise GrampsError("Ungültige JSON-Antwort von Gramps Web") from exc
            return raw
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise GrampsError(f"Gramps Web API HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise GrampsError(f"Gramps-Web-Verbindung fehlgeschlagen: {exc.reason}") from exc


def start_gedcom_export(client: GrampsClient) -> dict[str, Any]:
    result = _call(client, "/api/exporters/ged/file", method="POST", data=b"")
    if not isinstance(result, dict):
        raise GrampsError("Gramps Web hat keine gültige Export-Aufgabe zurückgegeben")
    return result


def task_status(client: GrampsClient, task_id: str) -> dict[str, Any]:
    if not _TASK_ID.fullmatch(task_id):
        raise GrampsError("Ungültige Gramps-Task-ID")
    result = _call(client, f"/api/tasks/{quote(task_id, safe='._:-')}")
    if not isinstance(result, dict):
        raise GrampsError("Ungültiger Status der Gramps-Export-Aufgabe")
    return result


def processed_export_path(filename: str) -> str:
    filename = filename.strip()
    if not filename or filename in {".", ".."} or "/" in filename or "\\" in filename or "\x00" in filename:
        raise GrampsError("Ungültiger Exportdateiname")
    return _PROCESSED_PREFIX + quote(filename, safe="._-")


def download_result(client: GrampsClient, path: str) -> bytes:
    if not path.startswith(_PROCESSED_PREFIX):
        raise GrampsError("Ungültiger Exportpfad")
    filename = path[len(_PROCESSED_PREFIX):]
    path = processed_export_path(filename)
    result = _call(client, path)
    if not isinstance(result, bytes):
        raise GrampsError("Exportdatei konnte nicht geladen werden")
    return result


def import_gedcom(client: GrampsClient, filename: str, content: bytes) -> dict[str, Any]:
    if not content:
        raise GrampsError("GEDCOM-Datei ist leer")
    boundary = "----Familienportal" + uuid.uuid4().hex
    safe_name = filename.replace('"', "").replace("\r", "").replace("\n", "").replace("/", "_").replace("\\", "_")
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{safe_name}\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    result = _call(client, "/api/importers/ged/file", method="POST", data=body, content_type=f"multipart/form-data; boundary={boundary}")
    if not isinstance(result, dict):
        raise GrampsError("Gramps Web hat keine gültige Import-Aufgabe zurückgegeben")
    return result
