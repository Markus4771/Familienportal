from familienportal.integration_admin import integration_summary


def test_integration_summary_for_admin_dashboard():
    rows = [
        {"configured": True, "enabled": True, "health_status": "healthy"},
        {"configured": True, "enabled": True, "health_status": "error"},
        {"configured": False, "enabled": False, "health_status": "not_checked"},
    ]
    result = integration_summary(rows)
    assert result["total"] == 3
    assert result["configured"] == 2
    assert result["enabled"] == 2
    assert result["healthy"] == 1
    assert result["failing"] == 1
