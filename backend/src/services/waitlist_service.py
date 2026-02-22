"""Service layer for waitlist workflows."""

from __future__ import annotations

import secrets
import uuid
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.password import hash_password
from . import email_service


def _normalize_waitlist(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "name": metadata.get("name"),
        "status": str(metadata.get("status") or "pending").lower(),
        "notes": metadata.get("notes"),
        "createdAt": row.get("createdAt"),
    }


async def submit_waitlist_request(db: AsyncSession, *, email: str, name: str) -> dict[str, Any]:
    existing = (
        await db.execute(
            text(
                """
                SELECT "id", "email", "metadata", "createdAt"
                FROM "WaitlistRequest"
                WHERE LOWER("email") = LOWER(:email)
                LIMIT 1
                """
            ),
            {"email": email},
        )
    ).mappings().first()
    if existing:
        raise ValueError("Email already submitted to waitlist")

    metadata = {"name": name.strip(), "status": "pending", "notes": None}
    created = (
        await db.execute(
            text(
                """
                INSERT INTO "WaitlistRequest" ("id", "email", "metadata")
                VALUES (:id, :email, CAST(:metadata AS JSONB))
                RETURNING "id", "email", "metadata", "createdAt"
                """
            ),
            {"id": str(uuid.uuid4()), "email": email.strip().lower(), "metadata": json.dumps(metadata)},
        )
    ).mappings().first()
    await db.commit()
    if not created:
        raise ValueError("Unable to submit waitlist request")
    return _normalize_waitlist(dict(created))


async def list_waitlist_requests(db: AsyncSession, *, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        result = await db.execute(
            text(
                """
                SELECT "id", "email", "metadata", "createdAt"
                FROM "WaitlistRequest"
                WHERE COALESCE(LOWER("metadata"->>'status'), 'pending') = :status
                ORDER BY "createdAt" DESC
                """
            ),
            {"status": status.lower()},
        )
    else:
        result = await db.execute(
            text(
                """
                SELECT "id", "email", "metadata", "createdAt"
                FROM "WaitlistRequest"
                ORDER BY "createdAt" DESC
                """
            )
        )
    return [_normalize_waitlist(dict(row)) for row in result.mappings().all()]


async def approve_waitlist_request(
    db: AsyncSession,
    *,
    waitlist_id: str,
    admin_email: str,
) -> dict[str, Any]:
    waitlist_row = (
        await db.execute(
            text(
                """
                SELECT "id", "email", "metadata", "createdAt"
                FROM "WaitlistRequest"
                WHERE "id" = :waitlist_id
                LIMIT 1
                """
            ),
            {"waitlist_id": waitlist_id},
        )
    ).mappings().first()
    if not waitlist_row:
        raise ValueError("Waitlist request not found")

    waitlist = _normalize_waitlist(dict(waitlist_row))
    if waitlist["status"] != "pending":
        raise ValueError("Waitlist request already processed")

    existing_user = (
        await db.execute(
            text("SELECT id FROM talents WHERE LOWER(email) = LOWER(:email) AND deleted_at IS NULL LIMIT 1"),
            {"email": waitlist["email"]},
        )
    ).mappings().first()
    if existing_user:
        raise ValueError("User already exists for this email")

    temporary_password = secrets.token_urlsafe(12)
    first_name, _, last_name = str(waitlist.get("name") or "").partition(" ")
    created_user = (
        await db.execute(
            text(
                """
                INSERT INTO talents (email, first_name, last_name, password_hash, tier)
                VALUES (:email, :first_name, :last_name, :password_hash, :tier)
                RETURNING id
                """
            ),
            {
                "email": waitlist["email"],
                "first_name": first_name or None,
                "last_name": last_name or None,
                "password_hash": hash_password(temporary_password),
                "tier": "Trial",
            },
        )
    ).mappings().first()
    if not created_user:
        raise ValueError("Unable to create user from waitlist request")

    updated_metadata = {"name": waitlist.get("name"), "status": "approved", "notes": waitlist.get("notes"), "approvedBy": admin_email}
    updated_row = (
        await db.execute(
            text(
                """
                UPDATE "WaitlistRequest"
                SET "metadata" = CAST(:metadata AS JSONB)
                WHERE "id" = :waitlist_id
                RETURNING "id", "email", "metadata", "createdAt"
                """
            ),
            {"waitlist_id": waitlist_id, "metadata": json.dumps(updated_metadata)},
        )
    ).mappings().first()

    await db.commit()
    await email_service.send_waitlist_welcome_email(
        to_email=str(waitlist["email"]),
        full_name=str(waitlist.get("name") or ""),
        temporary_password=temporary_password,
    )

    if not updated_row:
        raise ValueError("Unable to approve waitlist request")
    approved = _normalize_waitlist(dict(updated_row))
    approved["user_id"] = created_user["id"]
    approved["temporary_password"] = temporary_password
    return approved


async def reject_waitlist_request(
    db: AsyncSession,
    *,
    waitlist_id: str,
    admin_email: str,
    notes: str | None = None,
) -> dict[str, Any]:
    waitlist_row = (
        await db.execute(
            text(
                """
                SELECT "id", "email", "metadata", "createdAt"
                FROM "WaitlistRequest"
                WHERE "id" = :waitlist_id
                LIMIT 1
                """
            ),
            {"waitlist_id": waitlist_id},
        )
    ).mappings().first()
    if not waitlist_row:
        raise ValueError("Waitlist request not found")

    waitlist = _normalize_waitlist(dict(waitlist_row))
    if waitlist["status"] != "pending":
        raise ValueError("Waitlist request already processed")

    updated_metadata = {"name": waitlist.get("name"), "status": "rejected", "notes": notes, "rejectedBy": admin_email}
    updated_row = (
        await db.execute(
            text(
                """
                UPDATE "WaitlistRequest"
                SET "metadata" = CAST(:metadata AS JSONB)
                WHERE "id" = :waitlist_id
                RETURNING "id", "email", "metadata", "createdAt"
                """
            ),
            {"waitlist_id": waitlist_id, "metadata": json.dumps(updated_metadata)},
        )
    ).mappings().first()
    await db.commit()
    if not updated_row:
        raise ValueError("Unable to reject waitlist request")
    return _normalize_waitlist(dict(updated_row))
