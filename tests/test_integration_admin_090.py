from datetime import datetime, timezone

from familienportal.integration_admin import definitions, health_age_seconds, integration_summary


def test_core_integrations_are_registered():
    keys = {item.key for item in definitions()}
    assert {"nextcloud", "mailcow", "gramps", "paperless"}.issubset(keys)


def test_integration_summary_counts_states():
    rows = [
        {"configured": True, "enabled": True, "health_status": "healthy"},
        {"configured": True, "enabled": True, "health_status": "error"},
        {"configured": False, "enabled": False, "health_status": "not_configured"},
    ]
    assert integration_summary(rows) == {"total": 3, "configured": 2, "enabled": 2, "healthy": 1, "failing": 1}


def test_health_age_handles_timezone_aware_values():
    checked = datetime(2026, 9, 15, 8, 0, tzinfo=timezone.utc)
    now = datetime(2026, 9, 15, 8, 1, tzinfo=timezone.utc)
    assert health_age_seconds(checked, now) == 60
