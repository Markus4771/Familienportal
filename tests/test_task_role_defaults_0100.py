from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from familienportal.api import DEFAULT_ROLES
from familienportal.database import Base
from familienportal.models import Family, Role
from familienportal.task_role_defaults import TASK_ROLE_DEFAULTS, apply_task_role_defaults


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


def test_existing_roles_receive_missing_task_permissions_without_losing_custom_rights():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    family_id = uuid4()
    with Session(engine) as db:
        db.add(Family(id=family_id, name="Bestand", slug="bestand"))
        db.add_all(
            [
                Role(family_id=family_id, name="Erwachsene", permissions="dashboard.read,custom.family", system_role=True),
                Role(family_id=family_id, name="Kind", permissions="dashboard.read,custom.child", system_role=True),
                Role(family_id=family_id, name="Gast", permissions="dashboard.read", system_role=True),
                Role(family_id=family_id, name="Administrator", permissions="*", system_role=True),
                Role(family_id=family_id, name="Eigene Rolle", permissions="custom.only", system_role=False),
            ]
        )
        db.commit()

        assert apply_task_role_defaults(db, family_id) == 3

        roles = {role.name: role for role in db.query(Role).filter(Role.family_id == family_id).all()}
        adult = set(roles["Erwachsene"].permissions.split(","))
        child = set(roles["Kind"].permissions.split(","))
        guest = set(roles["Gast"].permissions.split(","))
        assert "custom.family" in adult
        assert TASK_ROLE_DEFAULTS["Erwachsene"] <= adult
        assert "custom.child" in child
        assert TASK_ROLE_DEFAULTS["Kind"] <= child
        assert TASK_ROLE_DEFAULTS["Gast"] <= guest
        assert roles["Administrator"].permissions == "*"
        assert roles["Eigene Rolle"].permissions == "custom.only"

        assert apply_task_role_defaults(db, family_id) == 0
