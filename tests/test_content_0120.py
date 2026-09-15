from types import SimpleNamespace
from uuid import uuid4
import pytest

from familienportal.content_links import ContentLink, ContentLinkKind
from familienportal.content_sharing import add_share


class FakeDb:
    def __init__(self): self.added=[]
    def scalar(self, _query): return None
    def add(self, value): self.added.append(value)


def test_content_link_kind_must_match_source_and_target():
    note_id, task_id = uuid4(), uuid4()
    good = ContentLink(kind=ContentLinkKind.NOTE_TASK.value, note_id=note_id, task_id=task_id)
    bad = ContentLink(kind=ContentLinkKind.LIST_TASK.value, note_id=note_id, task_id=task_id)
    assert good.targets_are_valid()
    assert not bad.targets_are_valid()


def test_targeted_share_rejects_cross_family():
    family_a, family_b = uuid4(), uuid4()
    actor = SimpleNamespace(id=uuid4(), family_id=family_a)
    note = SimpleNamespace(id=uuid4(), family_id=family_a)
    other = SimpleNamespace(id=uuid4(), family_id=family_b)
    with pytest.raises(ValueError, match="family boundary"):
        add_share(FakeDb(), actor, note=note, user=other)


def test_targeted_share_records_only_ids_not_content():
    family = uuid4(); actor = SimpleNamespace(id=uuid4(), family_id=family)
    note = SimpleNamespace(id=uuid4(), family_id=family, title="Privat", content="Geheim")
    target = SimpleNamespace(id=uuid4(), family_id=family)
    db = FakeDb(); share = add_share(db, actor, note=note, user=target)
    assert share.note_id == note.id and share.user_id == target.id
    assert not hasattr(share, "title") and not hasattr(share, "content")
