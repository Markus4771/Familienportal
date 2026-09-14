from types import SimpleNamespace

from familienportal.permissions import has_permission


def user(*permissions: str, superadmin: bool = False):
    roles = [SimpleNamespace(permissions=value) for value in permissions]
    return SimpleNamespace(roles=roles, is_superadmin=superadmin)


def test_exact_permission():
    assert has_permission(user("calendar.read"), "calendar.read")


def test_namespace_wildcard():
    assert has_permission(user("calendar.*"), "calendar.write")


def test_global_wildcard():
    assert has_permission(user("*"), "support.admin")


def test_superadmin():
    assert has_permission(user(superadmin=True), "anything.manage")


def test_missing_permission():
    assert not has_permission(user("calendar.read"), "documents.read")
