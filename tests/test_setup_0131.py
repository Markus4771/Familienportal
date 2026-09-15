import pytest
from fastapi import HTTPException

from familienportal.setup_web import MIN_SETUP_PASSWORD_LENGTH, _validate_setup_input


def test_setup_rejects_short_password():
    with pytest.raises(HTTPException) as exc_info:
        _validate_setup_input(
            family_name="Familie Mustermann",
            admin_name="Admin",
            admin_email="admin@example.invalid",
            password="x" * (MIN_SETUP_PASSWORD_LENGTH - 1),
        )

    assert exc_info.value.status_code == 400
    assert str(MIN_SETUP_PASSWORD_LENGTH) in exc_info.value.detail


def test_setup_accepts_minimum_password_length():
    _validate_setup_input(
        family_name="Familie Mustermann",
        admin_name="Admin",
        admin_email="admin@example.invalid",
        password="x" * MIN_SETUP_PASSWORD_LENGTH,
    )


@pytest.mark.parametrize(
    ("family_name", "admin_name", "admin_email"),
    [
        ("   ", "Admin", "admin@example.invalid"),
        ("Familie Mustermann", "   ", "admin@example.invalid"),
        ("Familie Mustermann", "Admin", "   "),
    ],
)
def test_setup_rejects_blank_required_fields(family_name, admin_name, admin_email):
    with pytest.raises(HTTPException) as exc_info:
        _validate_setup_input(
            family_name=family_name,
            admin_name=admin_name,
            admin_email=admin_email,
            password="x" * MIN_SETUP_PASSWORD_LENGTH,
        )

    assert exc_info.value.status_code == 400
