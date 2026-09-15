from familienportal.api import DEFAULT_ROLES
from familienportal.task_role_defaults import TASK_ROLE_DEFAULTS


def permissions(role):
    return set(DEFAULT_ROLES[role].split(","))


def test_administrator_keeps_full_access():
    assert DEFAULT_ROLES["Administrator"] == "*"


def test_adults_can_manage_family_tasks():
    rights = permissions("Erwachsene")
    assert {"tasks.read", "tasks.create", "tasks.edit", "tasks.assign", "tasks.complete", "tasks.delete", "tasks.manage"} <= rights


def test_children_can_work_with_own_tasks_but_not_manage_or_assign():
    rights = permissions("Kind")
    assert {"tasks.read", "tasks.create", "tasks.edit", "tasks.complete"} <= rights
    assert "tasks.manage" not in rights
    assert "tasks.assign" not in rights
    assert "tasks.delete" not in rights
    assert "tasks.private.read" not in rights


def test_guests_are_read_only():
    rights = permissions("Gast")
    assert "tasks.read" in rights
    assert not any(right in rights for right in {"tasks.create", "tasks.edit", "tasks.complete", "tasks.delete", "tasks.manage"})


def test_upgrade_defaults_match_role_policy():
    assert TASK_ROLE_DEFAULTS["Kind"] == {"tasks.read", "tasks.create", "tasks.edit", "tasks.complete"}
    assert TASK_ROLE_DEFAULTS["Gast"] == {"tasks.read"}
