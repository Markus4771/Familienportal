from familienportal.genealogy_privacy import visible_person


class User:
    is_superadmin = False
    roles = []


def test_api_privacy_hide_filters_living_person():
    person = {"handle": "P1", "name": "Lebend", "birth": "2000-01-01"}
    assert visible_person(User(), person, "hide", 110) is None


def test_api_privacy_redact_removes_birth_and_private_data():
    person = {"handle": "P1", "name": "Lebend", "birth": "2000-01-01", "email": "private@example.test"}
    result = visible_person(User(), person, "redact", 110)
    assert result is not None
    assert result["handle"] == "P1"
    assert "birth" not in result
    assert "email" not in result


def test_deceased_person_remains_visible():
    person = {"handle": "P2", "name": "Verstorben", "death": "2020-01-01"}
    assert visible_person(User(), person, "hide", 110) == person
