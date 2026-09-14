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


def remove_user_mapping(db: Session, family_id: UUID, user_id: UUID) -> bool:
    item = db.scalar(select(MailcowUserMapping).where(MailcowUserMapping.family_id == family_id, MailcowUserMapping.user_id == user_id))
    if not item:
        return False
    db.delete(item)
    db.flush()
    return True


def provision_mailbox(client: MailcowClient, *, address: str, name: str, password: str, quota_mb: int = 3072, force_password_update: bool = True) -> None:
    client.create_mailbox(address=address, name=name, password=password, quota_mb=quota_mb, force_password_update=force_password_update)


def update_mailbox(client: MailcowClient, mailbox: str, *, name: str | None = None, quota_mb: int | None = None, active: bool | None = None) -> None:
    client.edit_mailbox(mailbox, name=name, quota_mb=quota_mb, active=active)


def reset_mailbox_password(client: MailcowClient, mailbox: str, password: str) -> None:
    if len(password) < 8:
        raise MailcowError("Das neue Passwort muss mindestens 8 Zeichen lang sein")
    client.edit_mailbox(mailbox, password=password)


def normalize_destinations(value: str) -> str:
    raw = value.replace(";", ",").replace("\n", ",")
    items = []
    for part in raw.split(","):
        address = part.strip().lower()
        if not address:
            continue
        if "@" not in address:
            raise MailcowError(f"Ungültige Zieladresse: {address}")
        if address not in items:
            items.append(address)
    if not items:
        raise MailcowError("Mindestens eine Zieladresse ist erforderlich")
    return ",".join(items)


def add_alias(client: MailcowClient, address: str, destination: str) -> None:
    if not address.strip():
        raise MailcowError("Alias muss angegeben werden")
    client.create_alias(address.strip().lower(), normalize_destinations(destination))
