from fastapi.testclient import TestClient

from familienportal.main import app

client = TestClient(app, base_url="http://localhost")


def test_runtime_endpoint_exposes_no_secret() -> None:
    response = client.get("/api/v1/system/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_scheme"] == "http"
    assert payload["request_host"] == "localhost"
    assert "session_secret_key" not in payload
    assert "trusted_proxies" not in payload


def test_unknown_host_is_rejected() -> None:
    response = client.get("/health", headers={"host": "untrusted.example"})

    assert response.status_code == 400
