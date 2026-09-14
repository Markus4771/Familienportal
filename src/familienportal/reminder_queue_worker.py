from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from familienportal.calendar_models import CalendarEvent
from familienportal.config import get_settings
from familienportal.database import SessionLocal
from familienportal.job_state import JobDelivery

logger = logging.getLogger("familienportal.reminder_queue_worker")
settings = get_settings()


def run_once() -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        events = db.scalars(
            select(CalendarEvent).where(
                CalendarEvent.deleted_at.is_(None),
                CalendarEvent.reminder_minutes.is_not(None),
                CalendarEvent.created_by_user_id.is_not(None),
                CalendarEvent.starts_at >= now - timedelta(hours=1),
            )
        ).all()
        for event in events:
            scheduled_for = event.starts_at - timedelta(minutes=event.reminder_minutes or 0)
            if scheduled_for > now:
                continue
            exists = db.scalar(select(JobDelivery).where(JobDelivery.event_id == event.id, JobDelivery.channel == "email"))
            if exists:
                continue
            db.add(JobDelivery(event_id=event.id, user_id=event.created_by_user_id, channel="email", scheduled_for=scheduled_for))
        db.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    while True:
        run_once()
        time.sleep(max(30, settings.worker_interval_seconds))


if __name__ == "__main__":
    main()
