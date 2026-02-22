"""Service layer for Team and TeamMember operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _normalize_member(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "teamId": row.get("teamId"),
        "userId": row.get("userId"),
        "agentId": row.get("agentId"),
        "role": str(row.get("role", "member")).lower(),
        "type": str(row.get("type", "HUMAN")).lower(),
        "createdAt": row.get("createdAt"),
    }


async def create_team(db: AsyncSession, *, owner_user_id: str, name: str, description: str | None) -> dict[str, Any]:
    """Create a team and its owner TeamMember row."""
    team_row = (
        await db.execute(
            text(
                """
                INSERT INTO "Team" ("name", "description")
                VALUES (:name, :description)
                RETURNING "id", "name", "description", "createdAt"
                """
            ),
            {"name": name, "description": description},
        )
    ).mappings().first()

    if not team_row:
        raise ValueError("Unable to create team")

    owner_row = (
        await db.execute(
            text(
                """
                INSERT INTO "TeamMember" ("teamId", "userId", "agentId", "role", "type")
                VALUES (:team_id, :user_id, NULL, 'owner', 'HUMAN')
                RETURNING "id", "teamId", "userId", "agentId", "role", "type", "createdAt"
                """
            ),
            {"team_id": team_row["id"], "user_id": owner_user_id},
        )
    ).mappings().first()

    await db.commit()

    payload = dict(team_row)
    payload["members"] = [_normalize_member(dict(owner_row))] if owner_row else []
    return payload


async def list_user_teams(db: AsyncSession, *, user_id: str) -> list[dict[str, Any]]:
    """List teams where the current user is a human team member."""
    result = await db.execute(
        text(
            """
            SELECT t."id", t."name", t."description", t."createdAt"
            FROM "Team" t
            JOIN "TeamMember" tm ON tm."teamId" = t."id"
            WHERE CAST(tm."userId" AS TEXT) = :user_id
            ORDER BY t."createdAt" DESC
            """
        ),
        {"user_id": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_team_with_members(db: AsyncSession, *, team_id: str, user_id: str) -> dict[str, Any] | None:
    """Return a team with all members, only if current user belongs to it."""
    team_row = (
        await db.execute(
            text(
                """
                SELECT t."id", t."name", t."description", t."createdAt"
                FROM "Team" t
                JOIN "TeamMember" tm ON tm."teamId" = t."id"
                WHERE t."id" = :team_id
                  AND CAST(tm."userId" AS TEXT) = :user_id
                LIMIT 1
                """
            ),
            {"team_id": team_id, "user_id": user_id},
        )
    ).mappings().first()

    if not team_row:
        return None

    members_result = await db.execute(
        text(
            """
            SELECT "id", "teamId", "userId", "agentId", "role", "type", "createdAt"
            FROM "TeamMember"
            WHERE "teamId" = :team_id
            ORDER BY "createdAt" ASC
            """
        ),
        {"team_id": team_id},
    )

    payload = dict(team_row)
    payload["members"] = [_normalize_member(dict(row)) for row in members_result.mappings().all()]
    return payload


async def add_member(
    db: AsyncSession,
    *,
    team_id: str,
    actor_user_id: str,
    member_type: str,
    role: str,
    user_id: str | None,
    agent_id: str | None,
) -> dict[str, Any]:
    """Add a human or agent member to a team, requiring actor owner/admin rights."""
    authorization = (
        await db.execute(
            text(
                """
                SELECT "id"
                FROM "TeamMember"
                WHERE "teamId" = :team_id
                  AND CAST("userId" AS TEXT) = :actor_user_id
                  AND LOWER("role") IN ('owner', 'admin')
                LIMIT 1
                """
            ),
            {"team_id": team_id, "actor_user_id": actor_user_id},
        )
    ).mappings().first()
    if not authorization:
        raise PermissionError("Only team owners/admins can add members")

    normalized_type = member_type.upper()
    normalized_role = role.lower()

    if normalized_type == "HUMAN" and not user_id:
        raise ValueError("userId is required for human members")
    if normalized_type == "AGENT" and not agent_id:
        raise ValueError("agentId is required for agent members")

    member_row = (
        await db.execute(
            text(
                """
                INSERT INTO "TeamMember" ("teamId", "userId", "agentId", "role", "type")
                VALUES (:team_id, :user_id, :agent_id, :role, :type)
                RETURNING "id", "teamId", "userId", "agentId", "role", "type", "createdAt"
                """
            ),
            {
                "team_id": team_id,
                "user_id": user_id if normalized_type == "HUMAN" else None,
                "agent_id": agent_id if normalized_type == "AGENT" else None,
                "role": normalized_role,
                "type": normalized_type,
            },
        )
    ).mappings().first()

    if not member_row:
        raise ValueError("Unable to add team member")

    await db.commit()
    return _normalize_member(dict(member_row))
