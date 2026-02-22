from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.api import admin as admin_api
from src.api.admin import router as admin_router
from src.api.compliance import router as compliance_router
from src.core.admin import require_admin
from src.core.database import get_db_session


@pytest.fixture
def app_db() -> tuple[TestClient, AsyncMock]:
    app = FastAPI()
    app.include_router(admin_router)
    app.include_router(compliance_router)
    db = AsyncMock()
    db.commit = AsyncMock()

    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield db

    async def _override_admin() -> dict[str, str]:
        return {"id": "1", "email": "admin@example.com"}

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[require_admin] = _override_admin
    return TestClient(app), db


def test_compliance_audit_log_applies_entity_type_and_severity_filters(
    app_db: tuple[TestClient, AsyncMock],
) -> None:
    client, db = app_db
    result = AsyncMock()
    result.mappings.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result)

    response = client.get("/api/v1/compliance/audit-log?entity_type=user&severity=high")

    assert response.status_code == 200
    statement, params = db.execute.call_args.args
    query = str(statement)
    assert "entity_type" in query
    assert "severity" in query
    assert params["entity_type"] == "user"
    assert params["severity"] == "high"


def test_admin_update_user_auto_logs_audit_action(
    app_db: tuple[TestClient, AsyncMock],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, db = app_db
    update_result = AsyncMock()
    update_result.mappings.return_value.first.return_value = {"id": 7, "email": "u@example.com", "tier": "pro", "role": "admin"}
    db.execute = AsyncMock(return_value=update_result)
    mocked_log = AsyncMock()
    monkeypatch.setattr(admin_api, "log_admin_action", mocked_log)

    response = client.patch("/api/v1/admin/users/7", json={"role": "admin"})

    assert response.status_code == 200
    mocked_log.assert_awaited_once()
    assert mocked_log.await_args.kwargs["action"] == "user.updated"
