"""Admin authorization dependency for session-authenticated endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import validate_session
from .database import get_db_session

ADMIN_ROLE = "ADMIN"
SESSION_COOKIE_NAME = "session"


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Validate session and require ADMIN role for the resolved user."""
    session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    if not session_data or not session_data.get("userId"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(
        text(
            """
            SELECT id, email, role, tier
            FROM talents
            WHERE id = :user_id AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"user_id": int(session_data["userId"])},
    )
    user = result.mappings().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    if str(user.get("role") or "").upper() != ADMIN_ROLE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return dict(user)
