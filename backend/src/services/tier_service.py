"""Tier enforcement service for plan-based resource limits."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_session

_RESOURCE_LIMIT_COLUMNS = {
    "agents": "maxAgents",
    "conversations": "maxConversations",
}

_RESOURCE_COUNT_QUERIES = {
    "agents": """
        SELECT COUNT(*) AS total
        FROM project_agent_assignments paa
        JOIN project_orchestrations po ON po.id = paa.orchestration_id
        JOIN projects p ON p.id = po.project_id
        WHERE p.owner_id = :user_id
    """,
    "conversations": """
        SELECT COUNT(*) AS total
        FROM project_conversations pc
        JOIN project_orchestrations po ON po.id = pc.orchestration_id
        JOIN projects p ON p.id = po.project_id
        WHERE p.owner_id = :user_id
    """,
}


async def _fetch_tier_and_limits(db: AsyncSession, user_id: str) -> dict[str, Any]:
    """Resolve user tier limits from Subscription -> Tier with safe Trial fallback."""
    subscription_query = text(
        """
        SELECT t.name, t."maxAgents", t."maxConversations"
        FROM "Subscription" s
        JOIN "Tier" t ON t.id = s."tierId"
        WHERE CAST(s."userId" AS TEXT) = :user_id
        ORDER BY s."updatedAt" DESC NULLS LAST
        LIMIT 1
        """
    )
    try:
        tier_row = (await db.execute(subscription_query, {"user_id": user_id})).mappings().first()
    except Exception:
        tier_row = None

    if tier_row:
        return dict(tier_row)

    fallback_query = text(
        """
        SELECT t.name, t."maxAgents", t."maxConversations"
        FROM talents ta
        JOIN "Tier" t ON LOWER(t.name) = LOWER(COALESCE(ta.tier, 'Trial'))
        WHERE ta.id = :user_id
        LIMIT 1
        """
    )
    fallback_row = (await db.execute(fallback_query, {"user_id": int(user_id)})).mappings().first()
    if fallback_row:
        return dict(fallback_row)

    return {"name": "Trial", "maxAgents": 10, "maxConversations": 50}


async def _count_usage(db: AsyncSession, user_id: str, resource_type: str) -> int:
    """Count user usage for the requested resource type."""
    query = _RESOURCE_COUNT_QUERIES.get(resource_type)
    if not query:
        raise ValueError(f"Unsupported resource_type: {resource_type}")

    try:
        result = await db.execute(text(query), {"user_id": int(user_id)})
        count = result.scalar()
    except Exception:
        return 0
    return int(count or 0)


async def check_tier_limit(
    user: Mapping[str, Any],
    resource_type: str,
    db: AsyncSession | None = None,
) -> bool:
    """Return True when user can create resource under their current tier limits."""
    if resource_type not in _RESOURCE_LIMIT_COLUMNS:
        raise ValueError(f"Unsupported resource_type: {resource_type}")

    user_id = user.get("id") or user.get("userId")
    if user_id is None:
        return True

    limit_column = _RESOURCE_LIMIT_COLUMNS[resource_type]

    async def _check(session: AsyncSession) -> bool:
        tier = await _fetch_tier_and_limits(session, str(user_id))
        limit = tier.get(limit_column)
        if limit is None:
            return True
        usage = await _count_usage(session, str(user_id), resource_type)
        return usage < int(limit)

    if db is not None:
        return await _check(db)

    async with get_async_session() as session:
        return await _check(session)
