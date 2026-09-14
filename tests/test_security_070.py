from familienportal.auth_models import UserMfaState
from familienportal.auth_security import (
    consume_recovery_code,
    decrypt_seed,
    encrypt_seed,
    generate_recovery_codes,
    hash_verifier,
    store_recovery_codes,
    totp_code,
)
from familienportal.config import Settings


def test_totp_generation():
    seed = "JBSWY3DPEHPK3PXP"
    code = totp_code(seed, at=1_700_000_000)
    assert len(code) == 6
    assert code.isdigit()


def test_seed_encryption_roundtrip():
    settings = Settings(security_encryption_key="unit-test-security-key")
    encrypted = encrypt_seed("JBSWY3DPEHPK3PXP", settings)
    assert encrypted != "JBSWY3DPEHPK3PXP"
    assert decrypt_seed(encrypted, settings) == "JBSWY3DPEHPK3PXP"


def test_recovery_code_is_single_use():
    state = UserMfaState()
    codes = generate_recovery_codes(2)
    store_recovery_codes(state, codes)
    assert consume_recovery_code(state, codes[0]) is True
    assert consume_recovery_code(state, codes[0]) is False


def test_hash_verifier_is_stable_and_not_plaintext():
    value = "example-token"
    assert hash_verifier(value) == hash_verifier(value)
    assert hash_verifier(value) != value
