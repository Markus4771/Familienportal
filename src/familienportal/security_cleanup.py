from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_

from familienportal.auth_models import AccountRecoveryRequest, LoginSession, LoginThrottle
from familienportal.database import SessionLocal


def cleanup_security_records(retention_days: int = 30) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    with SessionLocal() as db:
        throttles = db.execute(
            delete(LoginThrottle).where(LoginThrottle.updated_at < cutoff)
        ).rowcount or 0
        recovery = db.execute(
            delete(AccountRecoveryRequest).where(
                or_(
                    AccountRecoveryRequest.expires_at < cutoff,
                    AccountRecoveryRequest.used_at < cutoff,
                )
            )
        ).rowcount or 0
        sessions = db.execute(
            delete(LoginSession).where(
                or_(
                    LoginSession.expires_at < cutoff,
                    LoginSession.revoked_at < cutoff,
                )
            )
        ).rowcount or 0
        db.commit()
    return {"throttles": throttles, "recovery": recovery, "sessions": sessions}


if __name__ == "__main__":
    result = cleanup_security_records()
    print(result)
