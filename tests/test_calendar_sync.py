from familienportal.calendar_sync import parse_event_ics


def test_parse_event_ics_reads_core_fields():
    payload = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "BEGIN:VEVENT",
        "UID:test-123",
        "DTSTART:20260914T120000Z",
        "DTEND:20260914T130000Z",
        "SUMMARY:Familientermin",
        "LOCATION:Landshut",
        "RRULE:FREQ=WEEKLY;INTERVAL=1",
        "END:VEVENT",
        "END:VCALENDAR",
    ])
    event = parse_event_ics(payload)
    assert event["uid"] == "test-123"
    assert event["title"] == "Familientermin"
    assert event["location"] == "Landshut"
    assert event["recurrence_rule"] == "FREQ=WEEKLY;INTERVAL=1"


def test_parse_event_ics_requires_uid_and_start():
    payload = "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nSUMMARY:Ohne UID\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    try:
        parse_event_ics(payload)
    except ValueError:
        return
    raise AssertionError("ValueError expected")
