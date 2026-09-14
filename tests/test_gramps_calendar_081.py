from datetime import date

from familienportal.gramps_calendar_dates import anniversary, desired_events, parse_gramps_date


def test_parse_gramps_date_variants():
    assert parse_gramps_date("1980-05-17") == date(1980, 5, 17)
    assert parse_gramps_date({"year": 1980, "month": 5, "day": 17}) == date(1980, 5, 17)
    assert parse_gramps_date([1980, 5, 17]) == date(1980, 5, 17)


def test_anniversary_handles_leap_day():
    assert anniversary(date(2000, 2, 29), 2027) == date(2027, 2, 28)
    assert anniversary(date(2000, 2, 29), 2028) == date(2028, 2, 29)


def test_desired_events_are_stable_and_cover_birth_and_death():
    people = [{"handle": "P1", "name": "Max Beispiel", "birth": "1980-05-17", "death": "2020-10-02"}]
    events = desired_events(people, 2026, years=2)
    assert set(events) == {
        "gramps:birthday:P1:2026",
        "gramps:birthday:P1:2027",
        "gramps:memorial:P1:2026",
        "gramps:memorial:P1:2027",
    }
    assert events["gramps:birthday:P1:2026"]["title"] == "Geburtstag: Max Beispiel"
    assert events["gramps:memorial:P1:2026"]["title"] == "Gedenktag: Max Beispiel"
