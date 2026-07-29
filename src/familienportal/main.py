from fastapi import FastAPI

from familienportal import __version__
from familienportal.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    debug=settings.debug,
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


@app.get("/api/v1/system/capabilities", tags=["system"])
async def capabilities() -> dict[str, object]:
    """Expose the capabilities already defined by the platform core."""

    return {
        "profiles": ["small_family", "extended_family"],
        "extension_types": ["module", "connector"],
        "planned_connectors": ["nextcloud", "mailcow"],
        "planned_modules": ["news", "marketplace", "support"],
    }
