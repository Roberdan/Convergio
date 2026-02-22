from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.prisma_models import AdminAuditLog
from src.services.audit_service import log_admin_action


@pytest.mark.asyncio
async def test_log_admin_action_persists_expected_payload() -> None:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    await log_admin_action(
        db=db,
        action="user.updated",
        entity_type="user",
        entity_id="42",
        admin_id="admin@example.com",
        details={"severity": "medium", "changes": {"role": "admin"}},
        ip="127.0.0.1",
    )

    db.add.assert_called_once()
    created_entry = db.add.call_args.args[0]
    assert isinstance(created_entry, AdminAuditLog)
    assert created_entry.action == "user.updated"
    assert created_entry.actor == "admin@example.com"
    assert created_entry.payload["entity_type"] == "user"
    assert created_entry.payload["entity_id"] == "42"
    assert created_entry.payload["severity"] == "medium"
    assert created_entry.payload["ip"] == "127.0.0.1"
    db.flush.assert_awaited_once()
