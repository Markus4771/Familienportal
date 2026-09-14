from __future__ import annotations

from datetime import datetime, timezone

from familienportal.calendar_models import CalendarEvent


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _unescape(value: str) -> str:
    return value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def _dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_dt(value: str) -> datetime:
    raw = value.strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Nicht unterstütztes ICS-Datum: {value}")


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


def parse_ics_events(payload: str) -> list[dict[str, object]]:
    unfolded: list[str] = []
    for line in payload.replace("\r\n", "\n").split("\n"):
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in unfolded:
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT" and current is not None:
            if current.get("title") and current.get("starts_at") and current.get("ends_at"):
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key_part, value = line.split(":", 1)
        key = key_part.split(";", 1)[0].upper()
        if key == "SUMMARY":
            current["title"] = _unescape(value)
        elif key == "DESCRIPTION":
            current["description"] = _unescape(value)
        elif key == "LOCATION":
            current["location"] = _unescape(value)
        elif key == "UID":
            current["external_uid"] = value.strip()
        elif key == "DTSTART":
            current["starts_at"] = _parse_dt(value)
        elif key == "DTEND":
            current["ends_at"] = _parse_dt(value)
        elif key == "RRULE":
            current["recurrence_rule"] = value.strip()
    return events
