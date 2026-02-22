"""Session-based authentication helpers backed by the DB Session table."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import structlog
except ImportError:  # pragma: no cover
    structlog = None

if structlog:
    logger = structlog.get_logger()
else:  # pragma: no cover
    import logging

    logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING

from .cookie_signing import sign_cookie, verify_cookie

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
else:
    AsyncSession = Any

DEFAULT_SESSION_TTL_SECONDS = 60 * 60 * 24 * 7


def _log_info(event: str, **kwargs: Any) -> None:
    if structlog:
        logger.info(event, **kwargs)
        return
    logger.info("%s | %s", event, kwargs)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def create_session(
    db_session: AsyncSession,
    user_id: str,
    *,
    session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ip: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Create DB session record and return signed cookie containing session token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=session_ttl_seconds)

    try:
        await db_session.execute(
            """
            INSERT INTO "Session" ("token", "userId", "expiresAt", "ip", "userAgent")
            VALUES (:token, :user_id, :expires_at, :ip, :user_agent)
            """,
            {
                "token": token,
                "user_id": user_id,
                "expires_at": expires_at.replace(tzinfo=None),
                "ip": ip,
                "user_agent": user_agent,
            },
        )
    except Exception:
        await db_session.execute(
            """
            INSERT INTO "Session" ("token", "userId", "expiresAt")
            VALUES (:token, :user_id, :expires_at)
            """,
            {
                "token": token,
                "user_id": user_id,
                "expires_at": expires_at.replace(tzinfo=None),
            },
        )
    await db_session.commit()

    _log_info("Session created", user_id=user_id, expires_at=expires_at.isoformat())
    return sign_cookie(token)


async def validate_session(db_session: AsyncSession, signed_cookie: str | None) -> dict[str, Any] | None:
    """Validate signed cookie and return active DB session row if valid."""
    if not signed_cookie:
        return None

    token = verify_cookie(signed_cookie)
    if not token:
        return None

    try:
        result = await db_session.execute(
            """
            SELECT "id", "token", "userId", "expiresAt", "createdAt", "ip", "userAgent"
            FROM "Session"
            WHERE "token" = :token
            LIMIT 1
            """,
            {"token": token},
        )
    except Exception:
        result = await db_session.execute(
            """
            SELECT "id", "token", "userId", "expiresAt", "createdAt"
            FROM "Session"
            WHERE "token" = :token
            LIMIT 1
            """,
            {"token": token},
        )
    db_record = result.mappings().first()
    if db_record is None:
        _log_info("Session token not found")
        return None

    expires_at = _as_utc(db_record["expiresAt"])
    if expires_at <= datetime.now(UTC):
        _log_info("Session expired, deleting", token_prefix=token[:8])
        await db_session.execute(
            'DELETE FROM "Session" WHERE "token" = :token',
            {"token": token},
        )
        await db_session.commit()
        return None

    return dict(db_record)


async def destroy_session(db_session: AsyncSession, signed_cookie: str | None) -> bool:
    """Delete a session from DB using signed cookie value."""
    if not signed_cookie:
        return False

    token = verify_cookie(signed_cookie)
    if not token:
        return False

    result = await db_session.execute(
        'DELETE FROM "Session" WHERE "token" = :token',
        {"token": token},
    )
    await db_session.commit()

    rowcount: int = int(result.rowcount or 0)
    if rowcount > 0:
        _log_info("Session destroyed", token_prefix=token[:8])
        return True

    _log_info("Session destroy requested but token not found")
    return False
