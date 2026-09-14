from familienportal.calendar_ics import parse_ics_events


def test_parse_ics_event() -> None:
    payload = """BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:test-1\r\nDTSTART:20260920T100000Z\r\nDTEND:20260920T110000Z\r\nSUMMARY:Familientermin\r\nLOCATION:Zuhause\r\nRRULE:FREQ=WEEKLY;INTERVAL=1\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"""
    events = parse_ics_events(payload)
    assert len(events) == 1
    assert events[0]["external_uid"] == "test-1"
    assert events[0]["title"] == "Familientermin"
    assert events[0]["location"] == "Zuhause"
    assert events[0]["recurrence_rule"] == "FREQ=WEEKLY;INTERVAL=1"
