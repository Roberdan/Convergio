from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.src.services import waitlist_service


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


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_server() -> None:
    """Override global integration fixture for isolated unit tests."""
    return None


@pytest.mark.asyncio
async def test_submit_waitlist_request_creates_pending_request() -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row=None),
            _FakeResult(
                row={
                    "id": "wl-1",
                    "email": "new@example.com",
                    "metadata": {"name": "New User", "status": "pending", "notes": None},
                    "createdAt": "2026-02-22T10:00:00",
                }
            ),
        ]
    )

    created = await waitlist_service.submit_waitlist_request(fake_db, email="new@example.com", name="New User")

    assert created["status"] == "pending"
    assert created["email"] == "new@example.com"
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_approve_waitlist_request_creates_user_and_sends_welcome_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(
                row={
                    "id": "wl-1",
                    "email": "new@example.com",
                    "metadata": {"name": "New User", "status": "pending", "notes": None},
                    "createdAt": "2026-02-22T10:00:00",
                }
            ),
            _FakeResult(row=None),
            _FakeResult(row={"id": 101}),
            _FakeResult(
                row={
                    "id": "wl-1",
                    "email": "new@example.com",
                    "metadata": {"name": "New User", "status": "approved", "notes": None},
                    "createdAt": "2026-02-22T10:00:00",
                }
            ),
        ]
    )

    send_welcome = AsyncMock()
    monkeypatch.setattr(waitlist_service.email_service, "send_waitlist_welcome_email", send_welcome)
    monkeypatch.setattr(waitlist_service, "hash_password", lambda _: "hashed-password")

    result = await waitlist_service.approve_waitlist_request(fake_db, waitlist_id="wl-1", admin_email="admin@example.com")

    assert result["status"] == "approved"
    assert result["user_id"] == 101
    assert "temporary_password" in result
    send_welcome.assert_awaited_once()
    fake_db.commit.assert_awaited_once()
