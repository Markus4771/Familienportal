from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from familienportal import __version__
from familienportal.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    debug=settings.debug,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    https_only=settings.secure_cookies,
    same_site="lax",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return a minimal process health response."""

    return {
        "status": "ok",
        "application": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "profile": settings.default_profile,
    }


@app.get("/api/v1/system/runtime", tags=["system"])
async def runtime(request: Request) -> dict[str, object]:
    """Expose non-secret runtime information for proxy diagnostics."""

    return {
        "public_url": settings.public_url,
        "request_scheme": request.url.scheme,
        "request_host": request.url.hostname,
        "client": request.client.host if request.client else None,
        "secure_cookies": settings.secure_cookies,
        "trusted_hosts": settings.trusted_hosts,
    }


@app.get("/api/v1/system/capabilities", tags=["system"])
async def capabilities() -> dict[str, object]:
    """Expose the capabilities already defined by the platform core."""

    return {
        "profiles": ["small_family", "extended_family"],
        "extension_types": ["module", "connector"],
        "planned_connectors": ["nextcloud", "mailcow"],
        "planned_modules": ["news", "marketplace", "support"],
    }
