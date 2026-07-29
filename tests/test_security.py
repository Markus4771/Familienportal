from familienportal.security import hash_password, verify_password


def test_password_roundtrip() -> None:
    encoded = hash_password("SehrSicheresPasswort123!")
    assert verify_password("SehrSicheresPasswort123!", encoded)
    assert not verify_password("Falsch", encoded)


def test_password_minimum_length() -> None:
    try:
        hash_password("kurz")
    except ValueError:
        return
    raise AssertionError("Kurzes Passwort wurde akzeptiert")
