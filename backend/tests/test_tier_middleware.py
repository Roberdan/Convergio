from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import pytest

from src.core.database import get_db_session
from src.core.tier_middleware import require_tier_limit


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.core import tier_middleware

    app = FastAPI()

    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_db_session] = _override_db

    @app.post("/agents", dependencies=[Depends(require_tier_limit("agents"))])
    async def create_agent() -> dict[str, str]:
        return {"status": "ok"}

    monkeypatch.setattr(tier_middleware, "validate_session", AsyncMock(return_value={"userId": "10"}))
    monkeypatch.setattr(tier_middleware, "_fetch_user_by_id", AsyncMock(return_value={"id": 10}))

    return TestClient(app)


def test_require_tier_limit_returns_402_when_limit_exceeded(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.core import tier_middleware

    monkeypatch.setattr(tier_middleware, "check_tier_limit", AsyncMock(return_value=False))

    response = client.post("/agents", cookies={"session": "signed-cookie"})

    assert response.status_code == 402


def test_require_tier_limit_allows_when_within_limit(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.core import tier_middleware

    monkeypatch.setattr(tier_middleware, "check_tier_limit", AsyncMock(return_value=True))

    response = client.post("/agents", cookies={"session": "signed-cookie"})

    assert response.status_code == 200
