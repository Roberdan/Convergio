"""Tier limit dependency middleware for API endpoints."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.tier_service import check_tier_limit
from .auth import validate_session
from .database import get_db_session

SESSION_COOKIE_NAME = "session"


async def _fetch_user_by_id(db: AsyncSession, user_id: str | int) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
            SELECT id, email, tier
            FROM talents
            WHERE id = :user_id AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"user_id": int(user_id)},
    )
    row = result.mappings().first()
    return dict(row) if row else None


def require_tier_limit(resource_type: str) -> Callable[..., Awaitable[None]]:
    """Dependency factory that enforces per-tier limits for a resource."""

    async def _enforce(
        request: Request,
        db: AsyncSession = Depends(get_db_session),
    ) -> None:
        session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))

        # Preserve backward compatibility for endpoints that currently allow anonymous usage.
        if not session_data or not session_data.get("userId"):
            return

        user = await _fetch_user_by_id(db, session_data["userId"])
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        allowed = await check_tier_limit(user, resource_type, db)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"{resource_type} tier limit exceeded",
            )

    return _enforce
