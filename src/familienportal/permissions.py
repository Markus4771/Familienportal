from __future__ import annotations

from familienportal.models import User


def permission_set(user: User) -> set[str]:
    permissions: set[str] = set()
    for role in user.roles:
        permissions.update(item.strip() for item in role.permissions.split(",") if item.strip())
    return permissions


def has_permission(user: User, required: str) -> bool:
    if user.is_superadmin:
        return True
    permissions = permission_set(user)
    if "*" in permissions or required in permissions:
        return True
    namespace = required.split(".", 1)[0]
    return f"{namespace}.*" in permissions


def has_any_permission(user: User, *required: str) -> bool:
    return any(has_permission(user, item) for item in required)
