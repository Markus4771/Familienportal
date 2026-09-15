from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from familienportal.list_models import FamilyList, FamilyListItem
from familienportal.models import User


def _family_user(db: Session, family_id: UUID, user_id: UUID | None) -> UUID | None:
    if user_id is not None and db.scalar(select(User.id).where(User.id == user_id, User.family_id == family_id)) is None:
        raise ValueError("assignee outside family")
    return user_id


def add_item(db: Session, family_list: FamilyList, *, title: str, quantity: Decimal | None = None, unit: str | None = None, category: str | None = None, assignee_user_id: UUID | None = None, due_at: datetime | None = None, note: str | None = None) -> FamilyListItem:
    title = title.strip()
    if not title:
        raise ValueError("title required")
    position = int(db.scalar(select(func.coalesce(func.max(FamilyListItem.position), -1)).where(FamilyListItem.list_id == family_list.id)) or -1) + 1
    item = FamilyListItem(list_id=family_list.id, title=title, quantity=quantity, unit=(unit or "").strip() or None, category=(category or "").strip() or None, assignee_user_id=_family_user(db, family_list.family_id, assignee_user_id), due_at=due_at, note=(note or "").strip() or None, position=position)
    db.add(item)
    return item


def update_item(db: Session, family_list: FamilyList, item: FamilyListItem, *, title: str, quantity: Decimal | None, unit: str | None, category: str | None, assignee_user_id: UUID | None, due_at: datetime | None, note: str | None) -> FamilyListItem:
    if item.list_id != family_list.id:
        raise ValueError("item outside list")
    item.title = title.strip()
    if not item.title:
        raise ValueError("title required")
    item.quantity = quantity; item.unit = (unit or "").strip() or None; item.category = (category or "").strip() or None
    item.assignee_user_id = _family_user(db, family_list.family_id, assignee_user_id); item.due_at = due_at; item.note = (note or "").strip() or None
    return item


def move_item(item: FamilyListItem, *, position: int) -> FamilyListItem:
    item.position = max(0, position)
    return item
