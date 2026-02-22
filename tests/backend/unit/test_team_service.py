from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.src.services import team_service


class _FakeResult:
    def __init__(self, row: dict | None = None, rows: list[dict] | None = None) -> None:
        self._row = row
        self._rows = rows or []

    def mappings(self) -> "_FakeResult":
        return self

    def first(self) -> dict | None:
        return self._row

    def all(self) -> list[dict]:
        return self._rows


@pytest.mark.asyncio
async def test_create_team_creates_owner_membership() -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "team-1", "name": "Platform", "description": "Core", "createdAt": "2026-01-01T00:00:00"}),
            _FakeResult(row={"id": "member-1", "teamId": "team-1", "role": "owner", "type": "HUMAN", "userId": "42", "agentId": None}),
        ]
    )

    team = await team_service.create_team(fake_db, owner_user_id="42", name="Platform", description="Core")

    assert team["id"] == "team-1"
    assert team["members"][0]["role"] == "owner"
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_member_supports_human_and_agent() -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "team-1"}),
            _FakeResult(row={"id": "tm-human", "teamId": "team-1", "role": "member", "type": "HUMAN", "userId": "7", "agentId": None}),
            _FakeResult(row={"id": "team-1"}),
            _FakeResult(row={"id": "tm-agent", "teamId": "team-1", "role": "admin", "type": "AGENT", "userId": None, "agentId": "agent-9"}),
        ]
    )

    human = await team_service.add_member(
        fake_db,
        team_id="team-1",
        actor_user_id="42",
        member_type="human",
        role="member",
        user_id="7",
        agent_id=None,
    )
    agent = await team_service.add_member(
        fake_db,
        team_id="team-1",
        actor_user_id="42",
        member_type="agent",
        role="admin",
        user_id=None,
        agent_id="agent-9",
    )

    assert human["type"] == "human"
    assert agent["type"] == "agent"
