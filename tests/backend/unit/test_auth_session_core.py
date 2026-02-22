from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.core.cookie_signing import sign_cookie, verify_cookie
from backend.src.core.password import hash_password, verify_password
from backend.src.core.auth import create_session, destroy_session, validate_session


def test_cookie_signing_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    signed = sign_cookie("session-token")

    assert verify_cookie(signed) == "session-token"


def test_cookie_signing_rejects_tampering(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    signed = sign_cookie("session-token")
    tampered = signed[:-1] + ("a" if signed[-1] != "a" else "b")

    assert verify_cookie(tampered) is None


def test_password_hash_and_verify() -> None:
    password = "P@ssw0rd-123"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


@pytest.mark.asyncio
async def test_create_session_adds_db_record_and_returns_signed_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    db = AsyncMock()

    signed_cookie = await create_session(db, user_id="user-123", session_ttl_seconds=600)

    assert verify_cookie(signed_cookie) is not None
    db.execute.assert_awaited()
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_session_returns_active_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    token = "token-123"
    signed = sign_cookie(token)

    session_row = {
        "token": token,
        "expiresAt": datetime.now(UTC) + timedelta(minutes=30),
        "userId": "user-123",
    }
    result = MagicMock()
    result.mappings.return_value.first.return_value = session_row

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    validated = await validate_session(db, signed)

    assert validated == session_row


@pytest.mark.asyncio
async def test_validate_session_rejects_expired_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    token = "token-123"
    signed = sign_cookie(token)

    session_row = {
        "token": token,
        "expiresAt": datetime.now(UTC) - timedelta(seconds=1),
    }
    result = MagicMock()
    result.mappings.return_value.first.return_value = session_row

    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    validated = await validate_session(db, signed)

    assert validated is None
    assert db.execute.await_count >= 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_destroy_session_returns_false_for_invalid_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    db = AsyncMock()

    destroyed = await destroy_session(db, "invalid-cookie")

    assert destroyed is False
    db.execute.assert_not_called()
