from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PersonRef:
    handle: str | None
    name: str
    gramps_id: str | None = None


def _name(value: dict[str, Any]) -> str:
    profile = value.get("profile") if isinstance(value.get("profile"), dict) else {}
    return str(profile.get("name") or value.get("name") or value.get("display_name") or value.get("gramps_id") or "Person")


def person_ref(value: dict[str, Any] | None) -> PersonRef | None:
    if not isinstance(value, dict):
        return None
    return PersonRef(handle=value.get("handle"), name=_name(value), gramps_id=value.get("gramps_id"))


def family_handles(person: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("family_list", "families", "parent_family_list", "parent_families"):
        raw = person.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, dict) and item.get("handle"):
                    values.append(str(item["handle"]))
    return list(dict.fromkeys(values))


def relationship_summary(person: dict[str, Any], families: list[dict[str, Any]], people_by_handle: dict[str, dict[str, Any]]) -> dict[str, list[PersonRef]]:
    person_handle = str(person.get("handle") or "")
    parents: list[PersonRef] = []
    partners: list[PersonRef] = []
    children: list[PersonRef] = []

    def add_unique(target: list[PersonRef], value: PersonRef | None) -> None:
        if value is None:
            return
        key = (value.handle, value.name)
        if any((item.handle, item.name) == key for item in target):
            return
        target.append(value)

    for family in families:
        father = family.get("father_handle") or family.get("father")
        mother = family.get("mother_handle") or family.get("mother")
        child_refs = family.get("child_ref_list") or family.get("children") or []
        child_handles: list[str] = []
        if isinstance(child_refs, list):
            for child in child_refs:
                if isinstance(child, str):
                    child_handles.append(child)
                elif isinstance(child, dict):
                    handle = child.get("ref") or child.get("handle")
                    if handle:
                        child_handles.append(str(handle))

        if person_handle and person_handle in child_handles:
            for handle in (father, mother):
                if isinstance(handle, str):
                    add_unique(parents, person_ref(people_by_handle.get(handle)))

        if person_handle and person_handle in {father, mother}:
            other = mother if person_handle == father else father
            if isinstance(other, str):
                add_unique(partners, person_ref(people_by_handle.get(other)))
            for handle in child_handles:
                add_unique(children, person_ref(people_by_handle.get(handle)))

    return {"parents": parents, "partners": partners, "children": children}
