from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.admin import require_admin
from ..core.database import get_db_session

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])


@router.get("/audit-log")
async def get_compliance_audit_log(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    entity_type: str | None = None,
    severity: str | None = None,
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
    if entity_type:
        where_clauses.append('COALESCE("payload"->>\'entity_type\', \'\') = :entity_type')
        params["entity_type"] = entity_type
    if severity:
        where_clauses.append('COALESCE("payload"->>\'severity\', \'\') = :severity')
        params["severity"] = severity

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
