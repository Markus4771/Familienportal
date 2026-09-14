from datetime import date

from familienportal.calendar_ui_web import _period, _shift


def test_month_period() -> None:
    start, end, _, start_date, end_date = _period("month", date(2026, 9, 14))
    assert start_date == date(2026, 9, 1)
    assert end_date == date(2026, 9, 30)
    assert start.date() == start_date
    assert end.date() == date(2026, 10, 1)


def test_week_period_starts_monday() -> None:
    _, _, _, start_date, end_date = _period("week", date(2026, 9, 14))
    assert start_date == date(2026, 9, 14)
    assert end_date == date(2026, 9, 20)


def test_shift_month_across_year() -> None:
    assert _shift("month", date(2026, 12, 15), 1) == date(2027, 1, 1)
