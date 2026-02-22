from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.services import tier_service


@pytest.mark.asyncio
async def test_check_tier_limit_allows_when_under_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    db = AsyncMock()
    monkeypatch.setattr(
        tier_service,
        "_fetch_tier_and_limits",
        AsyncMock(return_value={"name": "Trial", "maxAgents": 10, "maxConversations": 50}),
    )
    monkeypatch.setattr(tier_service, "_count_usage", AsyncMock(return_value=9))

    assert await tier_service.check_tier_limit({"id": 1}, "agents", db) is True


@pytest.mark.asyncio
async def test_check_tier_limit_blocks_when_reaching_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    db = AsyncMock()
    monkeypatch.setattr(
        tier_service,
        "_fetch_tier_and_limits",
        AsyncMock(return_value={"name": "Trial", "maxAgents": 10, "maxConversations": 50}),
    )
    monkeypatch.setattr(tier_service, "_count_usage", AsyncMock(return_value=10))

    assert await tier_service.check_tier_limit({"id": "1"}, "agents", db) is False


@pytest.mark.asyncio
async def test_check_tier_limit_unlimited_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    db = AsyncMock()
    monkeypatch.setattr(
        tier_service,
        "_fetch_tier_and_limits",
        AsyncMock(return_value={"name": "Pro", "maxAgents": None, "maxConversations": None}),
    )

    assert await tier_service.check_tier_limit({"id": 1}, "conversations", db) is True
