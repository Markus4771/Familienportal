from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.mailcow import MailcowClient, MailcowError
from familienportal.mailcow_models import MailcowUserMapping
from familienportal.models import User


def save_user_mapping(db: Session, family_id: UUID, user_id: UUID, mailbox: str) -> MailcowUserMapping:
    user = db.get(User, user_id)
    if not user or user.family_id != family_id:
        raise ValueError("Benutzer nicht gefunden")
    value = mailbox.strip().lower()
    if not value or "@" not in value:
        raise ValueError("Ungültiges Postfach")
    item = db.scalar(select(MailcowUserMapping).where(MailcowUserMapping.family_id == family_id, MailcowUserMapping.user_id == user_id))
    if item:
        item.mailbox = value
        item.updated_at = datetime.now(timezone.utc)
    else:
        item = MailcowUserMapping(family_id=family_id, user_id=user_id, mailbox=value)
        db.add(item)
    db.flush()
    return item


def provision_mailbox(client: MailcowClient, *, address: str, name: str, password: str, quota_mb: int = 3072, force_password_update: bool = True) -> None:
    client.create_mailbox(address=address, name=name, password=password, quota_mb=quota_mb, force_password_update=force_password_update)


def update_mailbox(client: MailcowClient, mailbox: str, *, name: str | None = None, quota_mb: int | None = None, active: bool | None = None) -> None:
    client.edit_mailbox(mailbox, name=name, quota_mb=quota_mb, active=active)


def add_alias(client: MailcowClient, address: str, destination: str) -> None:
    if not address.strip() or not destination.strip():
        raise MailcowError("Alias und Ziel müssen angegeben werden")
    client.create_alias(address, destination)
