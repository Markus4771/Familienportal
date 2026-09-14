from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json_dict
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement

from familienportal.auth_models import PasskeyCredential
from familienportal.config import Settings
from familienportal.models import User


def passkeys_for_user(db: Session, user_id) -> list[PasskeyCredential]:
    return list(db.scalars(select(PasskeyCredential).where(PasskeyCredential.user_id == user_id).order_by(PasskeyCredential.created_at)).all())


def registration_options(db: Session, user: User, settings: Settings) -> tuple[dict, str]:
    existing = passkeys_for_user(db, user.id)
    options = generate_registration_options(
        rp_id=settings.effective_webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.display_name,
        exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id)) for item in existing],
    )
    return options_to_json_dict(options), bytes_to_base64url(options.challenge)


def finish_registration(db: Session, user: User, settings: Settings, credential: dict, challenge: str, label: str) -> PasskeyCredential:
    verified = verify_registration_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(challenge),
        expected_rp_id=settings.effective_webauthn_rp_id,
        expected_origin=settings.effective_webauthn_origin,
        require_user_verification=True,
    )
    item = PasskeyCredential(
        user_id=user.id,
        credential_id=bytes_to_base64url(verified.credential_id),
        public_key=bytes_to_base64url(verified.credential_public_key),
        sign_count=verified.sign_count,
        label=(label.strip() or "Passkey")[:160],
    )
    db.add(item)
    db.flush()
    return item


def authentication_options(db: Session, user: User, settings: Settings) -> tuple[dict, str]:
    credentials = passkeys_for_user(db, user.id)
    options = generate_authentication_options(
        rp_id=settings.effective_webauthn_rp_id,
        allow_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id)) for item in credentials],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    return options_to_json_dict(options), bytes_to_base64url(options.challenge)


def finish_authentication(db: Session, user: User, settings: Settings, credential: dict, challenge: str) -> PasskeyCredential:
    credential_id = str(credential.get("id") or credential.get("rawId") or "")
    item = db.scalar(select(PasskeyCredential).where(PasskeyCredential.user_id == user.id, PasskeyCredential.credential_id == credential_id))
    if not item:
        raise ValueError("Passkey nicht gefunden")
    verified = verify_authentication_response(
        credential=credential,
        expected_challenge=base64url_to_bytes(challenge),
        expected_rp_id=settings.effective_webauthn_rp_id,
        expected_origin=settings.effective_webauthn_origin,
        credential_public_key=base64url_to_bytes(item.public_key),
        credential_current_sign_count=item.sign_count,
        require_user_verification=True,
    )
    item.sign_count = verified.new_sign_count
    item.last_used_at = datetime.now(timezone.utc)
    db.flush()
    return item
