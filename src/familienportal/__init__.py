"""Familienportal application package."""

__version__ = "0.3.0-dev"

# Register the platform management pages on the existing web router without
# coupling the FastAPI application bootstrap to individual platform features.
from familienportal.web import router as _web_router  # noqa: E402
from familienportal.platform_web import router as _platform_router  # noqa: E402

_web_router.include_router(_platform_router)
