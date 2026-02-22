"""Admin API endpoints for user management, audit and maintenance."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.admin import require_admin
from ..core.database import get_db_session

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class AdminUserUpdateRequest(BaseModel):
    tier: str | None = None
    role: str | None = None


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    offset = (page - 1) * page_size
    count_result = await db.execute(text('SELECT COUNT(*) AS count FROM talents WHERE deleted_at IS NULL'))
    total = int(count_result.scalar() or 0)

    users_result = await db.execute(
        text(
            """
            SELECT id, email, first_name, last_name, tier, role, created_at, updated_at
            FROM talents
            WHERE deleted_at IS NULL
            ORDER BY id ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"limit": page_size, "offset": offset},
    )
    users = [dict(row) for row in users_result.mappings().all()]
    return {
        "users": users,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        },
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clause = ", ".join([f"{field} = :{field}" for field in update_data])
    params = {"user_id": user_id, **update_data}
    result = await db.execute(
        text(
            f"""
            UPDATE talents
            SET {set_clause}, updated_at = NOW()
            WHERE id = :user_id AND deleted_at IS NULL
            RETURNING id, email, tier, role, updated_at
            """
        ),
        params,
    )
    updated = result.mappings().first()
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.execute(
        text(
            """
            INSERT INTO "AdminAuditLog" ("action", "actor", "payload")
            VALUES (:action, :actor, :payload)
            """
        ),
        {
            "action": "user.updated",
            "actor": str(admin_user.get("email") or admin_user.get("id")),
            "payload": {"entity": "user", "entity_id": str(user_id), "changes": update_data},
        },
    )
    await db.commit()
    return dict(updated)


@router.delete("/users/{user_id}")
async def soft_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    result = await db.execute(
        text(
            """
            UPDATE talents
            SET deleted_at = NOW(), updated_at = NOW()
            WHERE id = :user_id AND deleted_at IS NULL
            RETURNING id
            """
        ),
        {"user_id": user_id},
    )
    deleted = result.mappings().first()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.execute(
        text(
            """
            INSERT INTO "AdminAuditLog" ("action", "actor", "payload")
            VALUES (:action, :actor, :payload)
            """
        ),
        {
            "action": "user.deleted",
            "actor": str(admin_user.get("email") or admin_user.get("id")),
            "payload": {"entity": "user", "entity_id": str(user_id)},
        },
    )
    await db.commit()
    return {"message": "User deleted"}


@router.get("/audit-log")
async def get_audit_log(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    action: str | None = None,
    entity: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    where_clauses: list[str] = ["1=1"]
    params: dict[str, Any] = {"limit": page_size, "offset": (page - 1) * page_size}
    if start_date:
        where_clauses.append('"createdAt" >= :start_date')
        params["start_date"] = start_date
    if end_date:
        where_clauses.append('"createdAt" <= :end_date')
        params["end_date"] = end_date
    if action:
        where_clauses.append('"action" = :action')
        params["action"] = action
    if entity:
        where_clauses.append('COALESCE(CAST("payload" AS TEXT), \'\') LIKE :entity_like')
        params["entity_like"] = f'%\"entity\": \"{entity}\"%'

    result = await db.execute(
        text(
            f"""
            SELECT "id", "action", "actor", "payload", "createdAt"
            FROM "AdminAuditLog"
            WHERE {' AND '.join(where_clauses)}
            ORDER BY "createdAt" DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    )
    entries = [dict(row) for row in result.mappings().all()]
    return {"entries": entries, "page": page, "page_size": page_size}
