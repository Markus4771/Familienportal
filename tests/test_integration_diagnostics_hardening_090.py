from urllib.error import HTTPError

import pytest

import familienportal.integration_diagnostics as diagnostics


class FakeResponse:
    def __init__(self, code=200):
        self.code = code

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.code


def test_rejects_credentials_in_base_url():
    steps = diagnostics.diagnose_endpoint("https://user:password@example.test", enabled=True)
    assert steps[0].status == "error"


def test_head_not_supported_still_means_network_reachable(monkeypatch):
    def fail(*args, **kwargs):
        raise HTTPError("https://example.test", 405, "Method Not Allowed", {}, None)

    monkeypatch.setattr(diagnostics, "urlopen", fail)
    steps = diagnostics.diagnose_endpoint("https://example.test", enabled=True)
    network = next(step for step in steps if step.key == "network")
    assert network.status == "ok"


def test_successful_endpoint_is_network_ok(monkeypatch):
    monkeypatch.setattr(diagnostics, "urlopen", lambda *args, **kwargs: FakeResponse())
    steps = diagnostics.diagnose_endpoint("https://example.test", enabled=True)
    assert any(step.key == "network" and step.status == "ok" for step in steps)
