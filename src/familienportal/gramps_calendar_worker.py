from __future__ import annotations

import logging

from sqlalchemy import select

from familienportal.database import SessionLocal
from familienportal.gramps_calendar_sync import sync_gramps_calendar
from familienportal.gramps_web import _client
from familienportal.platform_models import ConnectorState

logger = logging.getLogger("familienportal.gramps_calendar_worker")


def run_once() -> dict[str, int]:
    totals = {"families": 0, "created": 0, "updated": 0, "deleted": 0, "unchanged": 0, "errors": 0}
    with SessionLocal() as db:
        states = db.scalars(select(ConnectorState).where(ConnectorState.connector_key == "gramps", ConnectorState.enabled.is_(True))).all()
        for state in states:
            try:
                people = _client(state).people(pagesize=200)
                result = sync_gramps_calendar(db, state.family_id, people)
                totals["families"] += 1
                for key in ("created", "updated", "deleted", "unchanged"):
                    totals[key] += result[key]
            except Exception:
                totals["errors"] += 1
                logger.exception("Gramps calendar sync failed for family %s", state.family_id)
    return totals


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_once())
