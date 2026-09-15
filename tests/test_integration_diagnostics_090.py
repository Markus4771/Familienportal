from familienportal.integration_diagnostics import diagnose_endpoint


def test_disabled_connector_stops_at_configuration():
    steps = diagnose_endpoint("https://example.invalid", enabled=False)
    assert len(steps) == 1
    assert steps[0].status == "disabled"


def test_missing_url_is_configuration_error():
    steps = diagnose_endpoint(None, enabled=True)
    assert steps[0].key == "configuration"
    assert steps[0].status == "error"


def test_invalid_scheme_is_rejected_without_network():
    steps = diagnose_endpoint("file:///etc/passwd", enabled=True)
    assert steps[0].status == "error"


def test_valid_url_has_configuration_step_first():
    # Use an unreachable local port; the assertion does not depend on external networking.
    steps = diagnose_endpoint("http://127.0.0.1:1", enabled=True, timeout=0.01)
    assert steps[0].key == "configuration"
    assert steps[0].status == "ok"
    assert any(step.key == "network" for step in steps)
