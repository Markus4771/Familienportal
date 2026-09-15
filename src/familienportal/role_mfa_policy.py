from __future__ import annotations

import os
from uuid import UUID

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from familienportal.auth_security import get_mfa_state
from familienportal.database import SessionLocal
from familienportal.models import User, UserStatus


ALLOWED_PREFIXES = ("/security", "/static", "/logout", "/health", "/ready")


def required_roles() -> set[str]:
    raw = os.getenv("FAMILIENPORTAL_MFA_REQUIRED_ROLES", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def session_user_id(request: Request) -> str | None:
    # SessionMiddleware stores the decoded session in scope. If this middleware
    # is ever ordered outside SessionMiddleware, fail closed without raising an
    # AssertionError during application startup or health requests.
    session = request.scope.get("session")
    if not isinstance(session, dict):
        return None
    value = session.get("user_id")
    return str(value) if value else None


class RoleMfaPolicyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        roles = required_roles()
        user_value = session_user_id(request)
        if not roles or not user_value or request.url.path.startswith(ALLOWED_PREFIXES):
            return await call_next(request)
        try:
            user_id = UUID(user_value)
        except (ValueError, TypeError):
            return await call_next(request)
        with SessionLocal() as db:
            user = db.get(User, user_id)
            if not user or user.status != UserStatus.ACTIVE.value:
                return await call_next(request)
            user_roles = {role.name for role in user.roles}
            if not user_roles.intersection(roles):
                return await call_next(request)
            state = get_mfa_state(db, user.id)
            if state and state.enabled:
                return await call_next(request)
        return RedirectResponse("/security?error=2FA+ist+für+Ihre+Rolle+vorgeschrieben", status_code=303)
