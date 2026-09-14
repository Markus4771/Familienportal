from datetime import datetime, timezone
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from familienportal.auth_models import LoginSession
from familienportal.database import SessionLocal


class SessionGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        user_id = request.session.get("user_id")
        session_id = request.session.get("session_id")
        if user_id and session_id:
            valid = False
            try:
                user_uuid = UUID(user_id)
                session_uuid = UUID(session_id)
            except ValueError:
                user_uuid = None
                session_uuid = None
            if user_uuid and session_uuid:
                with SessionLocal() as db:
                    item = db.get(LoginSession, session_uuid)
                    now = datetime.now(timezone.utc)
                    if item and item.user_id == user_uuid and item.revoked_at is None:
                        expires_at = item.expires_at
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=timezone.utc)
                        valid = expires_at > now
            if not valid:
                request.session.clear()
                if request.url.path.startswith("/api/"):
                    return JSONResponse({"detail": "Sitzung ungültig oder widerrufen"}, status_code=401)
                return RedirectResponse("/login", status_code=303)
        return await call_next(request)
