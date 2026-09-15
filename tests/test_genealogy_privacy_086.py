from familienportal.genealogy_privacy import is_living, redact_living, visible_person


class User:
    is_superadmin = False
    roles = []


def test_person_with_death_is_not_living():
    assert not is_living({"name": "Anna", "death": "2020-01-01"})


def test_recent_birth_without_death_is_living():
    assert is_living({"name": "Anna", "birth": "1990-01-01"})


def test_unknown_person_is_treated_as_living_fail_closed():
    assert is_living({"name": "Unbekannt"})


def test_configurable_age_threshold():
    assert not is_living({"name": "Anna", "birth": "1930-01-01"}, 80)
    assert is_living({"name": "Anna", "birth": "1930-01-01"}, 110)


def test_redaction_removes_sensitive_fields():
    person = {"name": "Anna", "birth": "1990-01-01", "email": "private@example.test", "notes": "privat"}
    redacted = redact_living(person)
    assert redacted["name"] == "Anna"
    assert "birth" not in redacted
    assert "email" not in redacted
    assert "notes" not in redacted


def test_hide_mode_removes_living_person():
    assert visible_person(User(), {"name": "Anna", "birth": "1990-01-01"}, "hide", 110) is None


def test_redact_mode_keeps_safe_person_record():
    result = visible_person(User(), {"name": "Anna", "birth": "1990-01-01", "email": "private@example.test"}, "redact", 110)
    assert result is not None
    assert result["name"] == "Anna"
    assert "email" not in result
