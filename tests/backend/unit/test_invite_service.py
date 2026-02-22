from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.src.services import invite_service


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
async def test_send_invite_creates_human_invite_and_sends_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "auth-1"}),
            _FakeResult(
                row={
                    "id": "inv-1",
                    "teamId": "team-1",
                    "email": "user@example.com",
                    "token": "tok-1",
                    "role": "member",
                    "status": "pending",
                    "type": "human",
                }
            ),
        ]
    )
    send_email = AsyncMock()
    monkeypatch.setattr(invite_service.email_service, "send_invite_email", send_email)

    invite = await invite_service.send_invite(
        fake_db,
        team_id="team-1",
        actor_user_id="42",
        invite_type="human",
        role="member",
        email="user@example.com",
        agent_id=None,
    )

    assert invite["status"] == "pending"
    send_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_invite_agent_adds_member_without_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "auth-1"}),
            _FakeResult(row={"id": "tm-1", "teamId": "team-1", "role": "admin", "type": "agent", "agentId": "agent-9"}),
        ]
    )
    send_email = AsyncMock()
    monkeypatch.setattr(invite_service.email_service, "send_invite_email", send_email)

    result = await invite_service.send_invite(
        fake_db,
        team_id="team-1",
        actor_user_id="42",
        invite_type="agent",
        role="admin",
        email=None,
        agent_id="agent-9",
    )

    assert result["type"] == "agent"
    send_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_accept_invite_adds_member_and_marks_accepted() -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "inv-1", "teamId": "team-1", "email": "user@example.com", "role": "member", "status": "pending", "type": "human"}),
            _FakeResult(row={"email": "user@example.com"}),
            _FakeResult(row={"id": "tm-1", "teamId": "team-1", "role": "member", "type": "HUMAN", "userId": "42", "agentId": None}),
            _FakeResult(row={"id": "inv-1", "status": "accepted"}),
        ]
    )

    invite = await invite_service.accept_invite(fake_db, invite_id="inv-1", actor_user_id="42")

    assert invite["status"] == "accepted"
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_invite_marks_rejected() -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": "inv-1", "email": "user@example.com", "status": "pending"}),
            _FakeResult(row={"email": "user@example.com"}),
            _FakeResult(
                row={
                    "id": "inv-1",
                    "teamId": "team-1",
                    "email": "user@example.com",
                    "token": "tok-1",
                    "role": "member",
                    "status": "rejected",
                    "type": "human",
                }
            ),
        ]
    )

    invite = await invite_service.reject_invite(fake_db, invite_id="inv-1", actor_user_id="42")

    assert invite["status"] == "rejected"
    fake_db.commit.assert_awaited_once()
