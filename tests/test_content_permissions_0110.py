from types import SimpleNamespace
from uuid import uuid4

from familienportal.list_permissions import can_read_list
from familienportal.note_permissions import can_read_note


def _user(family_id, user_id, permissions=(), superadmin=False):
    return SimpleNamespace(family_id=family_id, id=user_id, is_superadmin=superadmin, roles=[SimpleNamespace(permissions=",".join(permissions))])


def test_private_note_is_not_visible_to_other_normal_family_member(monkeypatch):
    family_id = uuid4(); owner_id = uuid4()
    owner = _user(family_id, owner_id, {"notes.read"})
    other = _user(family_id, uuid4(), {"notes.read"})
    note = SimpleNamespace(family_id=family_id, owner_user_id=owner_id, is_private=True)
    monkeypatch.setattr("familienportal.note_permissions.has_permission", lambda user, permission: permission in user.roles[0].permissions.split(","))
    assert can_read_note(owner, note)
    assert not can_read_note(other, note)


def test_family_boundaries_apply_to_notes_and_lists(monkeypatch):
    family_a = uuid4(); family_b = uuid4()
    user = _user(family_a, uuid4(), {"notes.read", "lists.read"})
    note = SimpleNamespace(family_id=family_b, owner_user_id=None, is_private=False)
    family_list = SimpleNamespace(family_id=family_b, owner_user_id=None, is_private=False)
    monkeypatch.setattr("familienportal.note_permissions.has_permission", lambda *_: True)
    monkeypatch.setattr("familienportal.list_permissions.has_permission", lambda *_: True)
    assert not can_read_note(user, note)
    assert not can_read_list(user, family_list)


def test_private_list_is_visible_to_owner(monkeypatch):
    family_id = uuid4(); owner_id = uuid4()
    owner = _user(family_id, owner_id, {"lists.read"})
    family_list = SimpleNamespace(family_id=family_id, owner_user_id=owner_id, is_private=True)
    monkeypatch.setattr("familienportal.list_permissions.has_permission", lambda user, permission: permission in user.roles[0].permissions.split(","))
    assert can_read_list(owner, family_list)
