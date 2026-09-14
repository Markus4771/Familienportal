from fastapi.testclient import TestClient

from familienportal.main import app


def test_health() -> None:
    client = TestClient(app, base_url="http://localhost")

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["application"] == "Familienportal"
    assert payload["profile"] in {"small_family", "extended_family"}
