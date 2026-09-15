from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from familienportal import __version__
from familienportal.admin_security_071 import router as admin_security_router
from familienportal.api import router as api_router
from familienportal.api_login_rate import router as api_login_rate_router
from familienportal.calendar_caldav_web import router as calendar_caldav_router
from familienportal.calendar_conflicts_web import router as calendar_conflicts_router
from familienportal.calendar_import_web import router as calendar_import_router
from familienportal.calendar_sync_api import router as calendar_sync_api_router
from familienportal.calendar_ui_web import router as calendar_ui_router
from familienportal.calendar_web import router as calendar_router
from familienportal.config import get_settings
from familienportal.content_web import router as content_router
from familienportal.database import engine
from familienportal.login_mfa import router as login_mfa_router
from familienportal.login_rate_web import router as login_rate_router
from familienportal.mailcow_alias_api import router as mailcow_alias_router
from familienportal.mailcow_mailbox_api import router as mailcow_mailbox_router
from familienportal.mailcow_management_page import router as mailcow_management_router
from familienportal.mailcow_mapping_api import router as mailcow_mapping_router
from familienportal.mailcow_web import router as mailcow_router
from familienportal.mfa_rate_web import router as mfa_rate_router
from familienportal.module_web import router as module_router
from familienportal.nextcloud_management_web import router as nextcloud_management_router
from familienportal.nextcloud_web import router as nextcloud_router
from familienportal.passkey_page import router as passkey_page_router
from familienportal.platform_web import router as platform_router
from familienportal.security_web import router as security_router
from familienportal.session_guard import SessionGuardMiddleware
from familienportal.tasks_web import router as tasks_router
from familienportal.totp_qr_web import router as totp_qr_router
from familienportal.webauthn_web import router as webauthn_router
from familienportal.web import router as web_router

settings = get_settings()
package_dir = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_name, version=__version__, debug=settings.debug)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(SessionGuardMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key, https_only=settings.secure_cookies, same_site="lax", max_age=settings.session_max_age_seconds)
app.mount("/static", StaticFiles(directory=package_dir / "static"), name="static")

# 0.7.1 policies are intentionally registered before legacy routes with the same paths.
app.include_router(login_rate_router)
app.include_router(mfa_rate_router)
app.include_router(api_login_rate_router)
app.include_router(webauthn_router)
app.include_router(passkey_page_router)
app.include_router(totp_qr_router)
app.include_router(admin_security_router)

app.include_router(web_router)
app.include_router(tasks_router)
app.include_router(content_router)
app.include_router(login_mfa_router)
app.include_router(security_router)
app.include_router(platform_router)
app.include_router(nextcloud_router)
app.include_router(nextcloud_management_router)
app.include_router(mailcow_router)
app.include_router(mailcow_management_router)
app.include_router(mailcow_mapping_router)
app.include_router(mailcow_mailbox_router)
app.include_router(mailcow_alias_router)
app.include_router(calendar_router)
app.include_router(calendar_ui_router)
app.include_router(calendar_conflicts_router)
app.include_router(calendar_caldav_router)
app.include_router(calendar_import_router)
app.include_router(calendar_sync_api_router)
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
    except SQLAlchemyError:
        return {"status": "not-ready"}
    return {"status": "ready"}


@app.get("/api/v1/system/runtime", tags=["system"])
def runtime() -> dict[str, object]:
    return {"version": __version__, "environment": settings.environment, "debug": settings.debug, "profile": settings.default_profile}


@app.get("/api/v1/system/capabilities", tags=["system"])
def capabilities() -> dict[str, object]:
    return {
        "application": settings.app_name,
        "version": __version__,
        "modules": ["calendar", "tasks", "notes", "lists", "news", "documents", "chat", "marketplace", "integrations"],
        "connectors": ["nextcloud", "mailcow", "home-assistant", "matrix", "mqtt", "immich", "jellyfin", "paperless-ngx", "gramps-web"],
    }


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception):
    return {"detail": "Not found"}
