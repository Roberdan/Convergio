from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.api.invites import router as invites_router
from backend.src.core.database import get_db_session


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(invites_router, prefix="/api/v1")
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


def test_create_invite_requires_authenticated_session(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import invites

    monkeypatch.setattr(invites, "validate_session", AsyncMock(return_value=None))

    response = client.post("/api/v1/invites", json={"teamId": "team-1", "type": "human", "email": "x@example.com", "role": "member"})

    assert response.status_code == 401


def test_create_invite_human_returns_created(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import invites

    monkeypatch.setattr(invites, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(
        invites.invite_service,
        "send_invite",
        AsyncMock(return_value={"id": "inv-1", "teamId": "team-1", "email": "u@example.com", "status": "pending", "role": "member", "type": "human"}),
    )

    response = client.post(
        "/api/v1/invites",
        json={"teamId": "team-1", "type": "human", "email": "u@example.com", "role": "member"},
        cookies={"session": "signed"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "inv-1"


def test_get_pending_invites_returns_items(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import invites

    monkeypatch.setattr(invites, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(invites.invite_service, "list_pending_invites", AsyncMock(return_value=[{"id": "inv-1", "status": "pending", "type": "human", "teamId": "team-1", "email": "u@example.com", "role": "member"}]))

    response = client.get("/api/v1/invites?teamId=team-1", cookies={"session": "signed"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_accept_invite_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import invites

    monkeypatch.setattr(invites, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(
        invites.invite_service,
        "accept_invite",
        AsyncMock(return_value={"id": "inv-1", "teamId": "team-1", "email": "u@example.com", "status": "accepted", "role": "member", "type": "human"}),
    )

    response = client.post("/api/v1/invites/inv-1/accept", cookies={"session": "signed"})

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_reject_invite_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import invites

    monkeypatch.setattr(invites, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(
        invites.invite_service,
        "reject_invite",
        AsyncMock(return_value={"id": "inv-1", "teamId": "team-1", "email": "u@example.com", "status": "rejected", "role": "member", "type": "human"}),
    )

    response = client.post("/api/v1/invites/inv-1/reject", cookies={"session": "signed"})

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
