from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.api.auth import router as auth_router
from backend.src.core.database import get_db_session


class _FakeResult:
    def __init__(self, row: dict | None = None) -> None:
        self._row = row

    def mappings(self) -> "_FakeResult":
        return self

    def first(self) -> dict | None:
        return self._row


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def fake_db() -> AsyncMock:
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def client(app: FastAPI, fake_db: AsyncMock) -> TestClient:
    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield fake_db

    app.dependency_overrides[get_db_session] = _override_db
    return TestClient(app)


def test_register_creates_trial_user_and_sets_session_cookie(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import auth

    fake_db.execute = AsyncMock(side_effect=[_FakeResult({"id": 101})])
    monkeypatch.setattr(auth, "create_session", AsyncMock(return_value="signed-cookie"))

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@user.com", "password": "TestPass-123", "full_name": "New User"},
    )

    assert response.status_code == 201
    assert response.json()["tier"] == "Trial"
    assert "session=" in response.headers["set-cookie"]


def test_login_rejects_invalid_credentials(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import auth

    fake_db.execute = AsyncMock(return_value=_FakeResult({"id": 10, "email": "a@b.com", "password_hash": "hash"}))
    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: False)

    response = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "bad-pass"})

    assert response.status_code == 401


def test_logout_clears_cookie(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import auth

    monkeypatch.setattr(auth, "destroy_session", AsyncMock(return_value=True))

    response = client.post("/api/v1/auth/logout", cookies={"session": "signed-cookie"})

    assert response.status_code == 200
    assert "session=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_me_returns_current_user(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import auth

    monkeypatch.setattr(auth, "validate_session", AsyncMock(return_value={"userId": "42"}))
    fake_db.execute = AsyncMock(return_value=_FakeResult({"id": 42, "email": "me@test.com", "tier": "Trial"}))

    response = client.get("/api/v1/auth/me", cookies={"session": "signed-cookie"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"


def test_change_password_rate_limited_after_three_attempts(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import auth

    auth._CHANGE_PASSWORD_ATTEMPTS.clear()
    monkeypatch.setattr(auth, "validate_session", AsyncMock(return_value={"userId": "7"}))
    fake_db.execute = AsyncMock(return_value=_FakeResult({"id": 7, "password_hash": "hash"}))
    monkeypatch.setattr(auth, "verify_password", lambda plain, hashed: False)

    payload = {"old_password": "old", "new_password": "new-pass-1"}
    assert client.post("/api/v1/auth/change-password", json=payload, cookies={"session": "s"}).status_code == 400
    assert client.post("/api/v1/auth/change-password", json=payload, cookies={"session": "s"}).status_code == 400
    assert client.post("/api/v1/auth/change-password", json=payload, cookies={"session": "s"}).status_code == 400

    limited = client.post("/api/v1/auth/change-password", json=payload, cookies={"session": "s"})
    assert limited.status_code == 429


def test_forgot_password_sends_reset_email(
    client: TestClient,
    fake_db: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import auth

    fake_db.execute = AsyncMock(return_value=_FakeResult({"id": 15, "email": "user@test.com"}))
    sender = AsyncMock()
    monkeypatch.setattr(auth, "_send_reset_email_via_resend", sender)

    response = client.post("/api/v1/auth/forgot-password", json={"email": "user@test.com"})

    assert response.status_code == 200
    sender.assert_awaited_once()


def test_reset_password_rejects_invalid_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/reset-password", json={"token": "invalid", "new_password": "BrandNew-123"})
    assert response.status_code == 400
