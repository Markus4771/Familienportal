from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select

from familienportal.permissions import has_permission
from familienportal.platform_models import FamilySetting

KEY_MODE = "genealogy.privacy.living_mode"
KEY_AGE = "genealogy.privacy.living_age_years"


def _profile(person: dict[str, Any]) -> dict[str, Any]:
    value = person.get("profile")
    return value if isinstance(value, dict) else person


def privacy_policy(db, family_id) -> tuple[str, int]:
    rows = db.scalars(select(FamilySetting).where(FamilySetting.family_id == family_id, FamilySetting.setting_key.in_([KEY_MODE, KEY_AGE]))).all()
    values = {row.setting_key: row.value for row in rows}
    mode = values.get(KEY_MODE, "redact")
    if mode not in {"redact", "hide"}:
        mode = "redact"
    try:
        age = min(130, max(80, int(values.get(KEY_AGE, "110"))))
    except ValueError:
        age = 110
    return mode, age


def is_living(person: dict[str, Any], age_years: int = 110) -> bool:
    profile = _profile(person)
    death = profile.get("death") or person.get("death") or profile.get("death_date") or person.get("death_date")
    if death:
        return False
    living = profile.get("living", person.get("living"))
    if isinstance(living, bool):
        return living
    birth = profile.get("birth") or person.get("birth") or profile.get("birth_date") or person.get("birth_date")
    year = None
    if isinstance(birth, str) and len(birth) >= 4 and birth[:4].isdigit():
        year = int(birth[:4])
    elif isinstance(birth, dict):
        raw = birth.get("year") or birth.get("date")
        if isinstance(raw, int):
            year = raw
        elif isinstance(raw, str) and len(raw) >= 4 and raw[:4].isdigit():
            year = int(raw[:4])
    return year is None or date.today().year - year < age_years


def can_view_living(user, person: dict[str, Any], age_years: int = 110) -> bool:
    return not is_living(person, age_years) or user.is_superadmin or has_permission(user, "genealogy.living.read")


def redact_living(person: dict[str, Any]) -> dict[str, Any]:
    result = dict(person)
    profile = dict(_profile(person))
    name = profile.get("name") or result.get("name") or result.get("display_name") or "Lebende Person"
    safe_profile = {"name": name, "living": True}
    if "profile" in result and isinstance(result.get("profile"), dict):
        result["profile"] = safe_profile
    result["name"] = name
    result["display_name"] = name
    for key in ("birth", "birth_date", "death", "death_date", "address", "addresses", "email", "phone", "phones", "notes", "note", "attributes"):
        result.pop(key, None)
    return result


def visible_person(user, person: dict[str, Any], mode: str, age_years: int) -> dict[str, Any] | None:
    if can_view_living(user, person, age_years):
        return person
    if mode == "hide":
        return None
    return redact_living(person)
