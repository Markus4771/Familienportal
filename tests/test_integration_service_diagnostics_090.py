from types import SimpleNamespace

from familienportal.integration_service_diagnostics import diagnose_connector


def state(**values):
    defaults = {"connector_key": "nextcloud", "enabled": False, "base_url": None, "username": None, "secret_reference": None}
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_missing_state_is_configuration_error():
    steps = diagnose_connector(None)
    assert steps[0].status == "error"


def test_disabled_state_does_not_require_secret():
    steps = diagnose_connector(state(enabled=False, base_url="https://cloud.example.test"))
    assert steps[0].status == "disabled"


def test_invalid_url_stops_before_secret_lookup():
    steps = diagnose_connector(state(enabled=True, base_url="file:///tmp/x", secret_reference="TEST_SECRET"))
    assert steps[0].status == "error"
