from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from familienportal.caldav import CalDAVClient, CalDAVError
from familienportal.calendar_ics import event_to_ics
from familienportal.calendar_models import CalendarEvent
from familienportal.calendar_sync_models import CalendarEventSyncState, CalendarSyncBinding


def _unfold_ics(text: str) -> list[str]:
    raw = text.replace("\r\n", "\n").split("\n")
    lines: list[str] = []
    for line in raw:
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _parse_dt(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if "T" in value:
        return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
    return datetime.strptime(value[:8], "%Y%m%d").replace(tzinfo=timezone.utc)


def parse_event_ics(text: str) -> dict[str, object]:
    values: dict[str, str] = {}
    in_event = False
    for line in _unfold_ics(text):
        if line == "BEGIN:VEVENT":
            in_event = True
            continue
        if line == "END:VEVENT":
            break
        if not in_event or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.split(";", 1)[0].upper()
        if key in {"UID", "SUMMARY", "DESCRIPTION", "LOCATION", "DTSTART", "DTEND", "RRULE"}:
            values[key] = value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    if not values.get("UID") or not values.get("DTSTART"):
        raise ValueError("VEVENT ohne UID oder DTSTART")
    start = _parse_dt(values["DTSTART"])
    end = _parse_dt(values.get("DTEND", values["DTSTART"]))
    return {"uid": values["UID"], "title": values.get("SUMMARY", "Termin"), "description": values.get("DESCRIPTION") or None, "location": values.get("LOCATION") or None, "starts_at": start, "ends_at": end, "recurrence_rule": values.get("RRULE") or None}


def _event_vcalendar(event: CalendarEvent) -> str:
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Familienportal//CalDAV Sync 0.5.1//DE", event_to_ics(event), "END:VCALENDAR", ""])


def sync_binding(db: Session, client: CalDAVClient, binding: CalendarSyncBinding) -> dict[str, int]:
    stats = {"pulled": 0, "pushed": 0, "conflicts": 0, "deleted": 0}
    remote_objects = client.list_objects(binding.remote_href)
    remote_by_href = {item.href: item for item in remote_objects}
    local_events = db.scalars(select(CalendarEvent).where(CalendarEvent.calendar_id == binding.calendar_id)).all()
    states = db.scalars(select(CalendarEventSyncState).where(CalendarEventSyncState.binding_id == binding.id)).all()
    state_by_event = {item.event_id: item for item in states}
    state_by_href = {item.remote_href: item for item in states}

    for remote in remote_objects:
        try:
            parsed = parse_event_ics(remote.data)
        except ValueError:
            continue
        state = state_by_href.get(remote.href)
        if state:
            event = db.get(CalendarEvent, state.event_id)
            if not event:
                continue
            remote_changed = state.remote_etag != remote.etag
            local_changed = bool(state.last_local_updated_at and event.updated_at > state.last_local_updated_at)
            if event.deleted_at:
                try:
                    client.delete_object(state.remote_href, state.remote_etag)
                    db.delete(event)
                    stats["deleted"] += 1
                except CalDAVError as exc:
                    state.conflict = True
                    state.conflict_message = str(exc)
                    stats["conflicts"] += 1
                continue
            if remote_changed and local_changed:
                state.conflict = True
                state.conflict_message = "Lokal und in Nextcloud geändert; keine Seite überschrieben."
                stats["conflicts"] += 1
                continue
            if remote_changed:
                event.title = str(parsed["title"])
                event.description = parsed["description"]
                event.location = parsed["location"]
                event.starts_at = parsed["starts_at"]
                event.ends_at = parsed["ends_at"]
                event.recurrence_rule = parsed["recurrence_rule"]
                event.external_uid = str(parsed["uid"])
                event.source = "nextcloud"
                event.updated_at = datetime.now(timezone.utc)
                state.remote_etag = remote.etag
                state.last_local_updated_at = event.updated_at
                state.conflict = False
                state.conflict_message = None
                stats["pulled"] += 1
        else:
            event = CalendarEvent(family_id=binding.family_id, calendar_id=binding.calendar_id, title=str(parsed["title"]), description=parsed["description"], location=parsed["location"], starts_at=parsed["starts_at"], ends_at=parsed["ends_at"], recurrence_rule=parsed["recurrence_rule"], external_uid=str(parsed["uid"]), source="nextcloud")
            db.add(event)
            db.flush()
            sync_state = CalendarEventSyncState(event_id=event.id, binding_id=binding.id, remote_href=remote.href, remote_etag=remote.etag, last_local_updated_at=event.updated_at)
            db.add(sync_state)
            state_by_event[event.id] = sync_state
            state_by_href[remote.href] = sync_state
            stats["pulled"] += 1

    remote_hrefs = set(remote_by_href)
    for event in local_events:
        state = state_by_event.get(event.id)
        if event.deleted_at:
            if state and state.remote_href in remote_hrefs:
                try:
                    client.delete_object(state.remote_href, state.remote_etag)
                except CalDAVError as exc:
                    state.conflict = True
                    state.conflict_message = str(exc)
                    stats["conflicts"] += 1
                    continue
            db.delete(event)
            stats["deleted"] += 1
            continue
        if state and state.remote_href not in remote_hrefs and not state.deleted_remote:
            if event.updated_at > (state.last_local_updated_at or event.created_at):
                state.conflict = True
                state.conflict_message = "Termin wurde in Nextcloud gelöscht, lokal aber verändert."
                stats["conflicts"] += 1
            else:
                db.delete(event)
                state.deleted_remote = True
                stats["deleted"] += 1
            continue
        if state and state.conflict:
            continue
        local_changed = not state or not state.last_local_updated_at or event.updated_at > state.last_local_updated_at
        if not local_changed:
            continue
        if not event.external_uid:
            event.external_uid = f"{event.id}@familienportal"
        href = state.remote_href if state else f"{binding.remote_href.rstrip('/')}/{quote(event.external_uid, safe='')}.ics"
        try:
            new_etag = client.put_object(href, _event_vcalendar(event), state.remote_etag if state else None)
        except CalDAVError as exc:
            if state:
                state.conflict = True
                state.conflict_message = str(exc)
            stats["conflicts"] += 1
            continue
        if not state:
            state = CalendarEventSyncState(event_id=event.id, binding_id=binding.id, remote_href=href)
            db.add(state)
            state_by_event[event.id] = state
        state.remote_etag = new_etag
        state.last_local_updated_at = event.updated_at
        state.conflict = False
        state.conflict_message = None
        stats["pushed"] += 1

    binding.sync_token = client.get_sync_token(binding.remote_href)
    binding.last_sync_at = datetime.now(timezone.utc)
    binding.last_status = "conflict" if stats["conflicts"] else "ok"
    binding.last_message = f"Pull {stats['pulled']}, Push {stats['pushed']}, gelöscht {stats['deleted']}, Konflikte {stats['conflicts']}"
    db.commit()
    return stats
