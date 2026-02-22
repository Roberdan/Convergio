from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.api.teams import router as teams_router
from backend.src.core.database import get_db_session


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(teams_router, prefix="/api/v1")
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


def test_create_team_requires_authenticated_session(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import teams

    monkeypatch.setattr(teams, "validate_session", AsyncMock(return_value=None))

    response = client.post("/api/v1/teams", json={"name": "Platform", "description": "Core team"})

    assert response.status_code == 401


def test_create_team_returns_created_team(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import teams

    monkeypatch.setattr(teams, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(
        teams.team_service,
        "create_team",
        AsyncMock(
            return_value={
                "id": "team-1",
                "name": "Platform",
                "description": "Core team",
                "members": [{"teamId": "team-1", "role": "owner", "type": "human", "userId": "42", "agentId": None}],
            }
        ),
    )

    response = client.post("/api/v1/teams", json={"name": "Platform", "description": "Core team"}, cookies={"session": "signed"})

    assert response.status_code == 201
    assert response.json()["id"] == "team-1"


def test_add_member_accepts_human_and_agent_types(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.src.api import teams

    monkeypatch.setattr(teams, "validate_session", AsyncMock(return_value={"userId": "42"}))
    monkeypatch.setattr(
        teams.team_service,
        "add_member",
        AsyncMock(return_value={"id": "tm-1", "teamId": "team-1", "role": "member", "type": "human", "userId": "7", "agentId": None}),
    )

    human = client.post(
        "/api/v1/teams/team-1/members",
        json={"type": "human", "role": "member", "userId": "7"},
        cookies={"session": "signed"},
    )
    assert human.status_code == 201

    monkeypatch.setattr(
        teams.team_service,
        "add_member",
        AsyncMock(return_value={"id": "tm-2", "teamId": "team-1", "role": "admin", "type": "agent", "userId": None, "agentId": "agent-9"}),
    )

    agent = client.post(
        "/api/v1/teams/team-1/members",
        json={"type": "agent", "role": "admin", "agentId": "agent-9"},
        cookies={"session": "signed"},
    )
    assert agent.status_code == 201
