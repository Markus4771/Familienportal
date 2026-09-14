from fastapi import FastAPI
from fastapi.testclient import TestClient

from familienportal.security_http import CsrfOriginMiddleware, SecurityHeadersMiddleware


def hardened_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfOriginMiddleware)

    @app.get("/probe")
    def probe_get():
        return {"ok": True}

    @app.post("/probe")
    def probe_post():
        return {"ok": True}

    return app


def test_security_headers_are_added():
    client = TestClient(hardened_app(), base_url="http://localhost:8000")
    response = client.get("/probe")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_cross_origin_post_is_blocked():
    client = TestClient(hardened_app(), base_url="http://localhost:8000")
    response = client.post(
        "/probe",
        headers={"Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"},
    )
    assert response.status_code == 403


def test_same_origin_post_is_allowed():
    client = TestClient(hardened_app(), base_url="http://localhost:8000")
    response = client.post(
        "/probe",
        headers={"Origin": "http://localhost:8000", "Sec-Fetch-Site": "same-origin"},
    )
    assert response.status_code == 200
