from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from familienportal.content_share_models import ContentShare, ContentShareKind
from familienportal.list_models import FamilyList
from familienportal.models import Household, User
from familienportal.note_models import FamilyNote


def _target_matches(user: User, share: ContentShare) -> bool:
    return share.user_id == user.id or (share.household_id is not None and share.household_id == user.household_id)


def note_shared_with(db: Session, user: User, note: FamilyNote) -> bool:
    if user.family_id != note.family_id:
        return False
    return db.scalar(select(ContentShare.id).where(ContentShare.family_id == user.family_id, ContentShare.note_id == note.id, or_(ContentShare.user_id == user.id, ContentShare.household_id == user.household_id if user.household_id else False)).limit(1)) is not None


def list_shared_with(db: Session, user: User, family_list: FamilyList) -> bool:
    if user.family_id != family_list.family_id:
        return False
    return db.scalar(select(ContentShare.id).where(ContentShare.family_id == user.family_id, ContentShare.list_id == family_list.id, or_(ContentShare.user_id == user.id, ContentShare.household_id == user.household_id if user.household_id else False)).limit(1)) is not None


def add_share(db: Session, actor: User, *, note: FamilyNote | None = None, family_list: FamilyList | None = None, user: User | None = None, household: Household | None = None) -> ContentShare:
    source = note or family_list
    target = user or household
    if source is None or target is None or (note is not None and family_list is not None) or (user is not None and household is not None):
        raise ValueError("exactly one source and one target required")
    if actor.family_id != source.family_id or actor.family_id != target.family_id:
        raise ValueError("family boundary violation")
    existing = db.scalar(select(ContentShare).where(ContentShare.note_id == (note.id if note else None), ContentShare.list_id == (family_list.id if family_list else None), ContentShare.user_id == (user.id if user else None), ContentShare.household_id == (household.id if household else None)))
    if existing:
        return existing
    share = ContentShare(family_id=actor.family_id, kind=ContentShareKind.NOTE.value if note else ContentShareKind.LIST.value, note_id=note.id if note else None, list_id=family_list.id if family_list else None, user_id=user.id if user else None, household_id=household.id if household else None, created_by_user_id=actor.id)
    db.add(share)
    return share
