from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from familienportal.config import get_settings


SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(), usb=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; "
            "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
        )
        settings = get_settings()
        if settings.environment.lower() == "production" and settings.public_url.startswith("https://"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method.upper() in SAFE_METHODS:
            return await call_next(request)

        settings = get_settings()
        expected = urlparse(settings.public_url)
        expected_origin = f"{expected.scheme}://{expected.netloc}".rstrip("/")
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        supplied_origin: str | None = None
        if origin and origin != "null":
            supplied_origin = origin.rstrip("/")
        elif referer:
            parsed = urlparse(referer)
            supplied_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

        # Browser form/fetch requests must prove same-origin. Non-browser API clients
        # without Origin/Referer remain supported unless explicit browser headers exist.
        browser_request = bool(origin or referer or request.headers.get("sec-fetch-site"))
        if browser_request and supplied_origin != expected_origin:
            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "CSRF-Prüfung fehlgeschlagen"}, status_code=403)
            return PlainTextResponse("CSRF-Prüfung fehlgeschlagen", status_code=403)

        sec_fetch_site = request.headers.get("sec-fetch-site")
        if sec_fetch_site and sec_fetch_site not in {"same-origin", "none"}:
            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "Cross-Site-Anfrage blockiert"}, status_code=403)
            return PlainTextResponse("Cross-Site-Anfrage blockiert", status_code=403)

        return await call_next(request)
