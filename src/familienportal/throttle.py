import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.auth_models import LoginThrottle


def make_key(scope: str, subject: str, client_ip: str | None) -> str:
    value = f"{scope}:{subject.strip().lower()}:{client_ip or '-'}"
    return hashlib.sha256(value.encode()).hexdigest()


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def lock_seconds(db: Session, key: str) -> int:
    row = db.scalar(select(LoginThrottle).where(LoginThrottle.identifier_hash == key))
    if not row or not row.locked_until:
        return 0
    now = datetime.now(timezone.utc)
    until = _aware(row.locked_until)
    if until <= now:
        row.locked_until = None
        row.failures = 0
        row.window_started_at = now
        return 0
    return max(1, int((until - now).total_seconds()))


def fail(db: Session, key: str, *, maximum: int, window_minutes: int, lock_minutes: int) -> int:
    now = datetime.now(timezone.utc)
    row = db.scalar(select(LoginThrottle).where(LoginThrottle.identifier_hash == key))
    if not row:
        row = LoginThrottle(identifier_hash=key, failures=0, window_started_at=now, updated_at=now)
        db.add(row)
        db.flush()
    if now - _aware(row.window_started_at) > timedelta(minutes=window_minutes):
        row.failures = 0
        row.window_started_at = now
    row.failures += 1
    row.updated_at = now
    if row.failures >= maximum:
        row.locked_until = now + timedelta(minutes=lock_minutes)
    db.flush()
    return lock_seconds(db, key)


def clear(db: Session, key: str) -> None:
    row = db.scalar(select(LoginThrottle).where(LoginThrottle.identifier_hash == key))
    if row:
        db.delete(row)
        db.flush()
