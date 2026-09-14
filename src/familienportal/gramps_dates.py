from __future__ import annotations

from typing import Any


def _profile(person: dict[str, Any]) -> dict[str, Any]:
    value = person.get("profile")
    return value if isinstance(value, dict) else person


def life_dates(person: dict[str, Any]) -> dict[str, Any]:
    profile = _profile(person)
    birth = profile.get("birth") or person.get("birth")
    death = profile.get("death") or person.get("death")
    return {
        "handle": person.get("handle"),
        "gramps_id": person.get("gramps_id"),
        "name": profile.get("name") or person.get("name") or person.get("display_name") or person.get("gramps_id") or "Person",
        "birth": birth,
        "death": death,
    }


def birthday_and_memorial_rows(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [life_dates(person) for person in people]
    return [row for row in rows if row.get("birth") or row.get("death")]
