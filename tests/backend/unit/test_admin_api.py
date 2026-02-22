from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.src.api.admin import router as admin_router
from backend.src.core.admin import require_admin
from backend.src.core.database import get_db_session


class _FakeResult:
    def __init__(self, rows: list[dict] | None = None, row: dict | None = None) -> None:
        self._rows = rows or []
        self._row = row

    def mappings(self) -> "_FakeResult":
        return self

    def all(self) -> list[dict]:
        return self._rows

    def first(self) -> dict | None:
        return self._row

    def scalar(self) -> int:
        if self._row and "count" in self._row:
            return int(self._row["count"])
        return len(self._rows)


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(admin_router)
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

    async def _override_admin() -> dict[str, str]:
        return {"id": 1, "role": "ADMIN", "email": "admin@test.com"}

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[require_admin] = _override_admin
    return TestClient(app)


def test_list_admin_users_supports_pagination(client: TestClient, fake_db: AsyncMock) -> None:
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"count": 2}),
            _FakeResult(
                rows=[
                    {"id": 10, "email": "a@test.com", "tier": "Trial", "role": "MEMBER"},
                    {"id": 11, "email": "b@test.com", "tier": "Pro", "role": "ADMIN"},
                ]
            ),
        ]
    )

    response = client.get("/api/v1/admin/users?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 2
    assert len(payload["users"]) == 2


def test_patch_admin_user_updates_tier_and_role(client: TestClient, fake_db: AsyncMock) -> None:
    fake_db.execute = AsyncMock(
        side_effect=[
            _FakeResult(row={"id": 10, "email": "a@test.com", "tier": "Scale", "role": "ADMIN"}),
            _FakeResult(),
        ]
    )

    response = client.patch("/api/v1/admin/users/10", json={"tier": "Scale", "role": "ADMIN"})

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
    fake_db.commit.assert_awaited_once()


def test_delete_admin_user_soft_deletes(client: TestClient, fake_db: AsyncMock) -> None:
    fake_db.execute = AsyncMock(side_effect=[_FakeResult(row={"id": 10}), _FakeResult()])

    response = client.delete("/api/v1/admin/users/10")

    assert response.status_code == 200
    assert response.json()["message"] == "User deleted"
    fake_db.commit.assert_awaited_once()


def test_admin_audit_log_filters_by_action_and_entity(client: TestClient, fake_db: AsyncMock) -> None:
    fake_db.execute = AsyncMock(
        return_value=_FakeResult(
            rows=[
                {
                    "id": "0d59444f-4cb6-429b-9f4d-c9a7665d2ca6",
                    "action": "user.updated",
                    "actor": "admin@test.com",
                    "payload": {"entity": "user", "entity_id": "10"},
                    "createdAt": "2026-01-01T00:00:00",
                }
            ]
        )
    )

    response = client.get("/api/v1/admin/audit-log?action=user.updated&entity=user")

    assert response.status_code == 200
    assert response.json()["entries"][0]["action"] == "user.updated"
