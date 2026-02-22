from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.src.api.waitlist import router as waitlist_router
from backend.src.core.admin import require_admin
from backend.src.core.database import get_db_session


@pytest.fixture(scope="session", autouse=True)
def ensure_backend_server() -> None:
    """Override global integration fixture for isolated unit tests."""
    return None


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(waitlist_router)
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
        return {"id": "1", "email": "admin@example.com", "role": "ADMIN"}

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[require_admin] = _override_admin
    return TestClient(app)


def test_submit_waitlist_request_public_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import waitlist

    monkeypatch.setattr(
        waitlist.waitlist_service,
        "submit_waitlist_request",
        AsyncMock(return_value={"id": "wl-1", "email": "new@example.com", "name": "New User", "status": "pending"}),
    )

    response = client.post("/api/v1/waitlist", json={"email": "new@example.com", "name": "New User"})

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_admin_waitlist_approve_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import waitlist

    monkeypatch.setattr(
        waitlist.waitlist_service,
        "approve_waitlist_request",
        AsyncMock(return_value={"id": "wl-1", "email": "new@example.com", "name": "New User", "status": "approved", "user_id": 101}),
    )

    response = client.post("/api/v1/admin/waitlist/wl-1/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_admin_waitlist_reject_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.api import waitlist

    monkeypatch.setattr(
        waitlist.waitlist_service,
        "reject_waitlist_request",
        AsyncMock(return_value={"id": "wl-1", "email": "new@example.com", "name": "New User", "status": "rejected"}),
    )

    response = client.post("/api/v1/admin/waitlist/wl-1/reject", json={"notes": "Not a fit right now"})

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
