from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from familienportal import __version__
from familienportal.api import router as api_router
from familienportal.config import get_settings
from familienportal.database import engine
from familienportal.module_web import router as module_router
from familienportal.nextcloud_web import router as nextcloud_router
from familienportal.platform_web import router as platform_router
from familienportal.web import router as web_router

settings = get_settings()
package_dir = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_name, version=__version__, debug=settings.debug)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, https_only=settings.secure_cookies, same_site="lax", max_age=settings.session_max_age_seconds)
app.mount("/static", StaticFiles(directory=package_dir / "static"), name="static")
app.include_router(web_router)
app.include_router(platform_router)
app.include_router(nextcloud_router)
app.include_router(module_router)
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "application": settings.app_name, "version": __version__, "environment": settings.environment, "profile": settings.default_profile}


@app.get("/ready", tags=["system"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return {"status": "not_ready", "database": exc.__class__.__name__}
    return {"status": "ready", "database": "ok"}


@app.get("/api/v1/system/runtime", tags=["system"])
async def runtime(request: Request) -> dict[str, object]:
    return {"public_url": settings.public_url, "request_scheme": request.url.scheme, "request_host": request.url.hostname, "client": request.client.host if request.client else None, "secure_cookies": settings.secure_cookies, "trusted_hosts": settings.trusted_hosts, "database_backend": settings.database_backend}


@app.get("/api/v1/system/capabilities", tags=["system"])
async def capabilities() -> dict[str, object]:
    return {
        "profiles": ["small_family", "extended_family"],
        "extension_types": ["module", "connector"],
        "core": ["families", "households", "users", "roles", "sessions", "audit", "platform_management"],
        "connectors": ["nextcloud", "mailcow", "gramps", "homeassistant", "paperless", "immich"],
        "nextcloud": ["health", "users", "groups", "shares", "webdav", "caldav", "carddav"],
        "modules": ["calendar", "news", "marketplace", "support", "genealogy", "documents"],
    }
