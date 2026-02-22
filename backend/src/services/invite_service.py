"""Service layer for invite workflows."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from . import email_service


def _normalize_invite(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "teamId": row.get("teamId"),
        "email": row.get("email"),
        "token": row.get("token"),
        "role": str(row.get("role", "member")).lower(),
        "status": str(row.get("status", "pending")).lower(),
        "type": str(row.get("type", "human")).lower(),
        "createdAt": row.get("createdAt"),
        "expiresAt": row.get("expiresAt"),
    }


async def _assert_can_manage_invites(db: AsyncSession, *, team_id: str, actor_user_id: str) -> None:
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
        raise PermissionError("Only team owners/admins can manage invites")


async def send_invite(
    db: AsyncSession,
    *,
    team_id: str,
    actor_user_id: str,
    invite_type: str,
    role: str,
    email: str | None,
    agent_id: str | None,
) -> dict[str, Any]:
    """Send a human invite (email) or instantly add an agent member."""
    await _assert_can_manage_invites(db, team_id=team_id, actor_user_id=actor_user_id)

    normalized_type = invite_type.lower()
    normalized_role = role.lower()

    if normalized_type == "agent":
        if not agent_id:
            raise ValueError("agentId is required for agent invites")

        member_row = (
            await db.execute(
                text(
                    """
                    INSERT INTO "TeamMember" ("teamId", "userId", "agentId", "role", "type")
                    VALUES (:team_id, NULL, :agent_id, :role, 'AGENT')
                    RETURNING "id", "teamId", "userId", "agentId", "role", "type", "createdAt"
                    """
                ),
                {"team_id": team_id, "agent_id": agent_id, "role": normalized_role},
            )
        ).mappings().first()

        if not member_row:
            raise ValueError("Unable to add agent to team")

        await db.commit()
        return {
            "id": member_row.get("id"),
            "teamId": member_row.get("teamId"),
            "email": None,
            "role": str(member_row.get("role", "member")).lower(),
            "status": "accepted",
            "type": "agent",
            "agentId": member_row.get("agentId"),
        }

    if not email:
        raise ValueError("email is required for human invites")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=7)

    invite_row = (
        await db.execute(
            text(
                """
                INSERT INTO "Invite" ("teamId", "email", "token", "role", "status", "type", "expiresAt")
                VALUES (:team_id, :email, :token, :role, 'pending', 'human', :expires_at)
                RETURNING "id", "teamId", "email", "token", "role", "status", "type", "createdAt", "expiresAt"
                """
            ),
            {
                "team_id": team_id,
                "email": email,
                "token": token,
                "role": normalized_role,
                "expires_at": expires_at,
            },
        )
    ).mappings().first()

    if not invite_row:
        raise ValueError("Unable to create invite")

    await db.commit()

    invite = _normalize_invite(dict(invite_row))
    await email_service.send_invite_email(
        to_email=invite["email"],
        invite_id=invite["id"],
        token=invite["token"],
        team_id=invite["teamId"],
        role=invite["role"],
    )
    return invite


async def list_pending_invites(db: AsyncSession, *, team_id: str, actor_user_id: str) -> list[dict[str, Any]]:
    """List pending invites for a team."""
    await _assert_can_manage_invites(db, team_id=team_id, actor_user_id=actor_user_id)

    result = await db.execute(
        text(
            """
            SELECT "id", "teamId", "email", "token", "role", "status", "type", "createdAt", "expiresAt"
            FROM "Invite"
            WHERE "teamId" = :team_id
              AND LOWER("status") = 'pending'
            ORDER BY "createdAt" DESC
            """
        ),
        {"team_id": team_id},
    )
    return [_normalize_invite(dict(row)) for row in result.mappings().all()]


async def accept_invite(db: AsyncSession, *, invite_id: str, actor_user_id: str) -> dict[str, Any]:
    """Accept pending human invite if invite email matches current user email."""
    invite_row = (
        await db.execute(
            text(
                """
                SELECT "id", "teamId", "email", "token", "role", "status", "type", "expiresAt"
                FROM "Invite"
                WHERE "id" = :invite_id
                  AND LOWER("status") = 'pending'
                LIMIT 1
                """
            ),
            {"invite_id": invite_id},
        )
    ).mappings().first()
    if not invite_row:
        raise ValueError("Invite not found")

    user_row = (
        await db.execute(
            text(
                """
                SELECT email
                FROM talents
                WHERE id = :actor_user_id
                LIMIT 1
                """
            ),
            {"actor_user_id": int(actor_user_id)},
        )
    ).mappings().first()

    if not user_row or str(user_row.get("email", "")).lower() != str(invite_row.get("email", "")).lower():
        raise PermissionError("Invite does not belong to current user")

    await db.execute(
        text(
            """
            INSERT INTO "TeamMember" ("teamId", "userId", "agentId", "role", "type")
            VALUES (:team_id, :user_id, NULL, :role, 'HUMAN')
            """
        ),
        {
            "team_id": invite_row["teamId"],
            "user_id": actor_user_id,
            "role": str(invite_row.get("role", "member")).lower(),
        },
    )

    updated_row = (
        await db.execute(
            text(
                """
                UPDATE "Invite"
                SET "status" = 'accepted'
                WHERE "id" = :invite_id
                RETURNING "id", "teamId", "email", "token", "role", "status", "type", "createdAt", "expiresAt"
                """
            ),
            {"invite_id": invite_id},
        )
    ).mappings().first()

    await db.commit()
    if not updated_row:
        raise ValueError("Unable to accept invite")
    return _normalize_invite(dict(updated_row))


async def reject_invite(db: AsyncSession, *, invite_id: str, actor_user_id: str) -> dict[str, Any]:
    """Reject pending invite if invite email matches current user email."""
    invite_row = (
        await db.execute(
            text(
                """
                SELECT "id", "email", "status"
                FROM "Invite"
                WHERE "id" = :invite_id
                  AND LOWER("status") = 'pending'
                LIMIT 1
                """
            ),
            {"invite_id": invite_id},
        )
    ).mappings().first()
    if not invite_row:
        raise ValueError("Invite not found")

    user_row = (
        await db.execute(
            text("SELECT email FROM talents WHERE id = :actor_user_id LIMIT 1"),
            {"actor_user_id": int(actor_user_id)},
        )
    ).mappings().first()
    if not user_row or str(user_row.get("email", "")).lower() != str(invite_row.get("email", "")).lower():
        raise PermissionError("Invite does not belong to current user")

    updated_row = (
        await db.execute(
            text(
                """
                UPDATE "Invite"
                SET "status" = 'rejected'
                WHERE "id" = :invite_id
                RETURNING "id", "teamId", "email", "token", "role", "status", "type", "createdAt", "expiresAt"
                """
            ),
            {"invite_id": invite_id},
        )
    ).mappings().first()

    await db.commit()
    if not updated_row:
        raise ValueError("Unable to reject invite")
    return _normalize_invite(dict(updated_row))
