from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.api.webhooks import router as webhooks_router
from backend.src.core.database import get_db_session


def test_stripe_webhook_returns_400_without_signature() -> None:
    app = FastAPI()
    app.include_router(webhooks_router, prefix="/api/v1/webhooks")

    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_db_session] = _override_db
    client = TestClient(app)

    response = client.post("/api/v1/webhooks/stripe", data="{}")
    assert response.status_code == 400


def test_stripe_webhook_accepts_valid_signature(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(webhooks_router, prefix="/api/v1/webhooks")

    fake_db = AsyncMock()

    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield fake_db

    app.dependency_overrides[get_db_session] = _override_db

    handle_webhook = AsyncMock(return_value={"received": True, "type": "customer.subscription.updated"})
    monkeypatch.setattr("backend.src.api.webhooks.stripe_service.handle_webhook", handle_webhook)

    client = TestClient(app)
    response = client.post(
        "/api/v1/webhooks/stripe",
        data='{"id":"evt_1"}',
        headers={"stripe-signature": "sig_valid"},
    )

    assert response.status_code == 200
    assert response.json()["received"] is True
