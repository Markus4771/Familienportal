from uuid import uuid4

from familienportal.models import Role, User
from familienportal.task_models import FamilyTask
from familienportal.task_permissions import (
    can_complete_task,
    can_delete_task,
    can_edit_task,
    can_read_task,
    can_set_assignee,
)


def user(*permissions: str, family_id=None, superadmin=False):
    family_id = family_id or uuid4()
    item = User(
        id=uuid4(),
        family_id=family_id,
        email=f"{uuid4()}@example.test",
        display_name="Test",
        password_hash="x",
        is_superadmin=superadmin,
    )
    item.roles = [Role(id=uuid4(), family_id=family_id, name="Test", permissions=",".join(permissions))]
    return item


def task_for(actor, *, private=False, assignee=None):
    return FamilyTask(
        id=uuid4(),
        family_id=actor.family_id,
        creator_user_id=actor.id,
        assignee_user_id=assignee.id if assignee else None,
        title="Aufgabe",
        is_private=private,
    )


def test_cross_family_access_is_denied_even_with_normal_permissions():
    owner = user("tasks.read", "tasks.edit", "tasks.complete")
    outsider = user("tasks.read", "tasks.edit", "tasks.complete")
    item = task_for(owner)
    assert not can_read_task(outsider, item)
    assert not can_edit_task(outsider, item)
    assert not can_complete_task(outsider, item)


def test_private_task_is_visible_to_owner_without_family_read_permission():
    owner = user()
    item = task_for(owner, private=True)
    assert can_read_task(owner, item)


def test_private_task_is_hidden_from_other_family_member():
    family_id = uuid4()
    owner = user(family_id=family_id)
    other = user("tasks.read", family_id=family_id)
    item = task_for(owner, private=True)
    assert not can_read_task(other, item)


def test_assignee_can_complete_with_complete_permission():
    family_id = uuid4()
    owner = user(family_id=family_id)
    assignee = user("tasks.complete", family_id=family_id)
    item = task_for(owner, assignee=assignee)
    assert can_complete_task(assignee, item)


def test_owner_needs_edit_permission_to_edit():
    owner = user()
    item = task_for(owner)
    assert not can_edit_task(owner, item)
    editor = user("tasks.edit", family_id=owner.family_id)
    item.creator_user_id = editor.id
    assert can_edit_task(editor, item)


def test_owner_needs_delete_permission_to_delete():
    owner = user()
    item = task_for(owner)
    assert not can_delete_task(owner, item)
    owner.roles[0].permissions = "tasks.delete"
    assert can_delete_task(owner, item)


def test_user_without_assign_permission_can_assign_task_to_self_or_nobody():
    actor = user("tasks.create")
    assert can_set_assignee(actor, actor.id)
    assert can_set_assignee(actor, None)


def test_user_without_assign_permission_cannot_assign_task_to_another_user():
    family_id = uuid4()
    actor = user("tasks.create", family_id=family_id)
    other = user(family_id=family_id)
    assert not can_set_assignee(actor, other.id)


def test_assign_permission_allows_assignment_to_another_user():
    family_id = uuid4()
    actor = user("tasks.assign", family_id=family_id)
    other = user(family_id=family_id)
    assert can_set_assignee(actor, other.id)


def test_editor_without_assign_permission_cannot_change_other_assignee():
    family_id = uuid4()
    actor = user("tasks.edit", family_id=family_id)
    current = user(family_id=family_id)
    other = user(family_id=family_id)
    item = task_for(actor, assignee=current)
    assert can_set_assignee(actor, current.id, item)
    assert not can_set_assignee(actor, actor.id, item)
    assert not can_set_assignee(actor, other.id, item)
    assert not can_set_assignee(actor, None, item)


def test_assignment_check_rejects_cross_family_task():
    actor = user("tasks.assign")
    outsider = user()
    item = task_for(outsider)
    assert not can_set_assignee(actor, actor.id, item)
