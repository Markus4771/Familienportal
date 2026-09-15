import pytest

from familienportal.gramps import GrampsClient, GrampsError


def test_timeout_is_bounded():
    assert GrampsClient("https://gramps.example.test", "token", timeout=0).timeout == 1.0
    assert GrampsClient("https://gramps.example.test", "token", timeout=120).timeout == 60.0


def test_request_rejects_external_or_malformed_paths_before_network():
    client = GrampsClient("https://gramps.example.test", "token")
    for path in ("https://evil.example/api/people", "//evil.example/api/people", "/not-api/people", "/api/people\r\nX-Test: bad"):
        with pytest.raises(GrampsError):
            client._request(path)
