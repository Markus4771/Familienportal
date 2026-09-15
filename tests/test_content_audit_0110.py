import json
from types import SimpleNamespace
from uuid import uuid4

from familienportal.content_audit import audit_note


class FakeDb:
    def __init__(self): self.added = []
    def add(self, value): self.added.append(value)


def test_note_audit_never_contains_title_or_content():
    family_id, actor_id, note_id = uuid4(), uuid4(), uuid4()
    actor = SimpleNamespace(family_id=family_id, id=actor_id)
    note = SimpleNamespace(id=note_id, household_id=None, owner_user_id=actor_id, is_private=True, archived_at=None, title="Geheim", content="Sehr privater Inhalt")
    db = FakeDb()
    event = audit_note(db, "note.updated", actor, note)
    data = json.loads(event.details)
    assert "title" not in data
    assert "content" not in data
    assert "Geheim" not in event.details
    assert "Sehr privater Inhalt" not in event.details
