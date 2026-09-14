from __future__ import annotations

import logging
import time
from sqlalchemy import select

from familienportal.caldav import CalDAVClient
from familienportal.calendar_sync import sync_binding
from familienportal.calendar_sync_models import CalendarSyncBinding
from familienportal.config import get_settings
from familienportal.database import SessionLocal
from familienportal.nextcloud_web import _client as nextcloud_client
from familienportal.platform_models import ConnectorState

logger = logging.getLogger("familienportal.calendar_sync_worker")
settings = get_settings()


def run_once() -> None:
    with SessionLocal() as db:
        bindings = db.scalars(select(CalendarSyncBinding).where(CalendarSyncBinding.enabled.is_(True))).all()
        for binding in bindings:
            state = db.scalar(select(ConnectorState).where(ConnectorState.family_id == binding.family_id, ConnectorState.connector_key == "nextcloud"))
            if not state:
                continue
            try:
                nc = nextcloud_client(state)
                sync_binding(db, CalDAVClient(nc.base_url, nc.username, nc.password), binding)
            except Exception as exc:
                logger.exception("Sync failed for %s", binding.id)
                binding.last_status = "error"
                binding.last_message = str(exc)[:500]
                db.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    while True:
        run_once()
        time.sleep(max(60, settings.calendar_sync_interval_minutes * 60))


if __name__ == "__main__":
    main()
