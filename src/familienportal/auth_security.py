from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.auth_models import AccountRecoveryRequest, LoginSession, UserMfaState
from familienportal.config import Settings
from familienportal.models import User


def _fernet(settings: Settings) -> Fernet:
    digest = hashlib.sha256(settings.security_encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def encrypt_seed(seed: str, settings: Settings) -> str:
    return _fernet(settings).encrypt(seed.encode("utf-8")).decode("ascii")


def decrypt_seed(value: str, settings: Settings) -> str:
    return _fernet(settings).decrypt(value.encode("ascii")).decode("utf-8")


def new_totp_seed() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_code(seed: str, *, at: int | None = None, step: int = 30, digits: int = 6) -> str:
    timestamp = int(time.time() if at is None else at)
    counter = timestamp // step
    padded = seed + "=" * ((8 - len(seed) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10**digits)).zfill(digits)


def verify_totp(seed: str, code: str, *, window: int = 1) -> bool:
    normalized = "".join(ch for ch in code if ch.isdigit())
    if len(normalized) != 6:
        return False
    now = int(time.time())
    return any(hmac.compare_digest(totp_code(seed, at=now + offset * 30), normalized) for offset in range(-window, window + 1))


def otpauth_uri(user: User, seed: str, settings: Settings) -> str:
    issuer = quote(settings.mfa_issuer, safe="")
    label = quote(f"{settings.mfa_issuer}:{user.email}", safe="")
    return f"otpauth://totp/{label}?secret={seed}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


def hash_verifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_recovery_codes(count: int = 10) -> list[str]:
    return [f"{secrets.token_hex(3)}-{secrets.token_hex(3)}" for _ in range(count)]


def store_recovery_codes(state: UserMfaState, codes: list[str]) -> None:
    state.recovery_hashes_json = json.dumps([hash_verifier(code.lower()) for code in codes])


def consume_recovery_code(state: UserMfaState, code: str) -> bool:
    try:
        hashes = list(json.loads(state.recovery_hashes_json or "[]"))
    except (TypeError, ValueError):
        hashes = []
    candidate = hash_verifier(code.strip().lower())
    for stored in hashes:
        if hmac.compare_digest(stored, candidate):
            hashes.remove(stored)
            state.recovery_hashes_json = json.dumps(hashes)
            state.updated_at = datetime.now(timezone.utc)
            return True
    return False


def get_mfa_state(db: Session, user_id) -> UserMfaState | None:
    return db.scalar(select(UserMfaState).where(UserMfaState.user_id == user_id))


def create_session(db: Session, user: User, settings: Settings, user_agent: str | None = None) -> LoginSession:
    now = datetime.now(timezone.utc)
    item = LoginSession(
        user_id=user.id,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(seconds=settings.session_max_age_seconds),
        user_agent=(user_agent or "")[:500] or None,
    )
    db.add(item)
    db.flush()
    return item


def valid_session(db: Session, session_id, user_id) -> LoginSession | None:
    item = db.get(LoginSession, session_id)
    now = datetime.now(timezone.utc)
    if not item or item.user_id != user_id or item.revoked_at is not None or _utc(item.expires_at) <= now:
        return None
    item.last_seen_at = now
    return item


def revoke_all_sessions(db: Session, user_id, *, except_session_id=None) -> int:
    now = datetime.now(timezone.utc)
    items = db.scalars(select(LoginSession).where(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None))).all()
    count = 0
    for item in items:
        if except_session_id and item.id == except_session_id:
            continue
        item.revoked_at = now
        count += 1
    return count


def create_recovery_request(db: Session, user: User, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    db.add(AccountRecoveryRequest(
        user_id=user.id,
        verifier_hash=hash_verifier(token),
        expires_at=now + timedelta(minutes=settings.password_reset_ttl_minutes),
    ))
    db.flush()
    return token


def consume_recovery_request(db: Session, token: str) -> AccountRecoveryRequest | None:
    now = datetime.now(timezone.utc)
    item = db.scalar(select(AccountRecoveryRequest).where(AccountRecoveryRequest.verifier_hash == hash_verifier(token)))
    if not item or item.used_at is not None or _utc(item.expires_at) <= now:
        return None
    item.used_at = now
    return item
