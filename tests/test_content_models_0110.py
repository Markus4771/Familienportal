from uuid import uuid4

from familienportal.content_links import ContentLink
from familienportal.list_models import FamilyListItem, ListKind


def test_list_kinds_cover_family_use_cases():
    assert {kind.value for kind in ListKind} == {"general", "shopping", "packing", "wishlist"}


def test_list_item_supports_quantity_category_due_and_assignment():
    item = FamilyListItem(list_id=uuid4(), title="Milch", quantity=2, unit="l", category="Lebensmittel", assignee_user_id=uuid4())
    assert item.title == "Milch"
    assert item.quantity == 2
    assert item.unit == "l"
    assert item.category == "Lebensmittel"


def test_content_link_requires_one_source_and_one_target():
    note_id, list_id, task_id, event_id = uuid4(), uuid4(), uuid4(), uuid4()
    assert ContentLink(note_id=note_id, task_id=task_id).targets_are_valid()
    assert ContentLink(list_id=list_id, event_id=event_id).targets_are_valid()
    assert not ContentLink(note_id=note_id, list_id=list_id, task_id=task_id).targets_are_valid()
    assert not ContentLink(note_id=note_id, task_id=task_id, event_id=event_id).targets_are_valid()
