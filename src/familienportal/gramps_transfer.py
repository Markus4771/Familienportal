from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from familienportal.gramps import GrampsClient, GrampsError


def _call(client: GrampsClient, path: str, *, method: str = "GET", data: bytes | None = None, content_type: str | None = None) -> Any:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {client.access_token}", "User-Agent": "Familienportal/0.8"}
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(f"{client.base_url}{path}", method=method, data=data, headers=headers)
    try:
        with urlopen(request, timeout=client.timeout) as response:
            raw = response.read()
            if "application/json" in (response.headers.get("Content-Type") or ""):
                return json.loads(raw.decode("utf-8")) if raw else None
            return raw
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise GrampsError(f"Gramps Web API HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise GrampsError(f"Gramps-Web-Verbindung fehlgeschlagen: {exc.reason}") from exc


def start_gedcom_export(client: GrampsClient) -> dict[str, Any]:
    result = _call(client, "/api/exporters/ged/file", method="POST", data=b"")
    return result if isinstance(result, dict) else {}


def task_status(client: GrampsClient, task_id: str) -> dict[str, Any]:
    result = _call(client, f"/api/tasks/{task_id}")
    return result if isinstance(result, dict) else {}


def download_result(client: GrampsClient, path: str) -> bytes:
    result = _call(client, path)
    if not isinstance(result, bytes):
        raise GrampsError("Exportdatei konnte nicht geladen werden")
    return result


def import_gedcom(client: GrampsClient, filename: str, content: bytes) -> dict[str, Any]:
    boundary = "----Familienportal" + uuid.uuid4().hex
    safe_name = filename.replace('"', "").replace("\r", "").replace("\n", "")
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{safe_name}\"\r\n"
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    result = _call(client, "/api/importers/ged/file", method="POST", data=body, content_type=f"multipart/form-data; boundary={boundary}")
    return result if isinstance(result, dict) else {}
