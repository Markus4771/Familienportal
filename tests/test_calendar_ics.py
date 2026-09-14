from datetime import datetime, timezone
from uuid import uuid4

from familienportal.calendar_ics import calendar_to_ics
from familienportal.calendar_models import CalendarEvent


def test_calendar_ics_contains_event_and_recurrence() -> None:
    event = CalendarEvent(
        id=uuid4(),
        family_id=uuid4(),
        calendar_id=uuid4(),
        title="Familientermin",
        starts_at=datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc),
        recurrence_rule="FREQ=WEEKLY;INTERVAL=1",
        reminder_minutes=30,
    )
    payload = calendar_to_ics("Familie", [event])
    assert "BEGIN:VCALENDAR" in payload
    assert "SUMMARY:Familientermin" in payload
    assert "RRULE:FREQ=WEEKLY;INTERVAL=1" in payload
    assert "TRIGGER:-PT30M" in payload
