from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from familienportal.calendar_models import CalendarEvent


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def event_to_ics(event: CalendarEvent) -> str:
    uid = event.external_uid or f"{event.id}@familienportal"
    lines = [
        "BEGIN:VEVENT",
        f"UID:{_escape(uid)}",
        f"DTSTAMP:{_dt(datetime.now(timezone.utc))}",
        f"DTSTART:{_dt(event.starts_at)}",
        f"DTEND:{_dt(event.ends_at)}",
        f"SUMMARY:{_escape(event.title)}",
    ]
    if event.description:
        lines.append(f"DESCRIPTION:{_escape(event.description)}")
    if event.location:
        lines.append(f"LOCATION:{_escape(event.location)}")
    if event.recurrence_rule:
        lines.append(f"RRULE:{event.recurrence_rule}")
    if event.reminder_minutes is not None:
        lines.extend([
            "BEGIN:VALARM",
            f"TRIGGER:-PT{max(0, event.reminder_minutes)}M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(event.title)}",
            "END:VALARM",
        ])
    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def calendar_to_ics(name: str, events: list[CalendarEvent]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Familienportal//Calendar 0.5//DE",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape(name)}",
    ]
    lines.extend(event_to_ics(event) for event in events)
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
