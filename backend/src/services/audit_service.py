from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.prisma_models import AdminAuditLog


async def log_admin_action(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    admin_id: str,
    details: dict[str, Any] | None,
    ip: str | None,
) -> None:
    payload: dict[str, Any] = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "ip": ip,
        "severity": (details or {}).get("severity", "low"),
    }
    db.add(
        AdminAuditLog(
            id=uuid4(),
            action=action,
            actor=admin_id,
            payload=payload,
        )
    )
    await db.flush()
