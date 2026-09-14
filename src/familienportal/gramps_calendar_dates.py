from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from familienportal.gramps_dates import birthday_and_memorial_rows


def parse_gramps_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for candidate in (text[:10], text):
            try:
                return date.fromisoformat(candidate)
            except ValueError:
                pass
        return None
    if isinstance(value, dict):
        for key in ("date", "value", "iso", "dateval"):
            parsed = parse_gramps_date(value.get(key))
            if parsed:
                return parsed
        try:
            if value.get("year") and value.get("month") and value.get("day"):
                return date(int(value["year"]), int(value["month"]), int(value["day"]))
        except (TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return date(int(value[0]), int(value[1]), int(value[2]))
        except (TypeError, ValueError):
            return None
    return None


def anniversary(original: date, year: int) -> date:
    try:
        return original.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


def desired_events(people: list[dict[str, Any]], start_year: int, years: int = 3) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in birthday_and_memorial_rows(people):
        name = str(row.get("name") or row.get("gramps_id") or "Person").strip()
        handle = str(row.get("handle") or row.get("gramps_id") or name).strip()
        for kind, field, label in (("birthday", "birth", "Geburtstag"), ("memorial", "death", "Gedenktag")):
            original = parse_gramps_date(row.get(field))
            if not original:
                continue
            for year in range(start_year, start_year + max(1, years)):
                day = anniversary(original, year)
                start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
                uid = f"gramps:{kind}:{handle}:{year}"
                result[uid] = {
                    "title": f"{label}: {name}",
                    "description": f"Aus Gramps Web synchronisiert. Originaldatum: {original.isoformat()}",
                    "starts_at": start,
                    "ends_at": start + timedelta(days=1),
                    "category": kind,
                }
    return result
