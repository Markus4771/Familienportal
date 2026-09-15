from __future__ import annotations

from typing import Any


def _handle(value: Any) -> str | None:
    if isinstance(value, str):
        return value or None
    if isinstance(value, dict):
        for key in ("ref", "handle", "media_handle"):
            if value.get(key):
                return str(value[key])
    return None


def media_handles(person: dict[str, Any]) -> list[str]:
    values = person.get("media_list") or person.get("media") or person.get("media_refs") or []
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        handle = _handle(value)
        if handle and handle not in result:
            result.append(handle)
    return result


def normalize_media(item: dict[str, Any]) -> dict[str, str | None]:
    path = item.get("path") or item.get("file") or item.get("filename")
    mime = item.get("mime") or item.get("mime_type") or item.get("content_type")
    description = item.get("description") or item.get("desc")
    return {
        "handle": str(item.get("handle") or "") or None,
        "gramps_id": str(item.get("gramps_id") or "") or None,
        "title": str(item.get("description") or item.get("title") or item.get("gramps_id") or "Medium"),
        "path": str(path) if path else None,
        "mime": str(mime) if mime else None,
        "description": str(description) if description else None,
    }
