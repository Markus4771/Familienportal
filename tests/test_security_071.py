from familienportal.config import Settings
from familienportal.throttle import make_key
from familienportal.webauthn_service import authentication_options, registration_options


def test_webauthn_defaults_follow_public_url():
    settings = Settings(public_url="https://portal.example.de")
    assert settings.effective_webauthn_rp_id == "portal.example.de"
    assert settings.effective_webauthn_origin == "https://portal.example.de"


def test_webauthn_explicit_values_override_defaults():
    settings = Settings(
        public_url="https://portal.example.de",
        webauthn_rp_id="login.example.de",
        webauthn_origin="https://login.example.de",
    )
    assert settings.effective_webauthn_rp_id == "login.example.de"
    assert settings.effective_webauthn_origin == "https://login.example.de"


def test_throttle_key_is_stable_and_hides_input():
    first = make_key("password", "User@Example.de", "192.0.2.10")
    second = make_key("password", "user@example.de", "192.0.2.10")
    assert first == second
    assert "user@example.de" not in first
    assert len(first) == 64


def test_webauthn_service_is_importable():
    assert callable(registration_options)
    assert callable(authentication_options)
