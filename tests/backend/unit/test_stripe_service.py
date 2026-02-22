from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.src.services.stripe_service import StripeService


@pytest.mark.asyncio
async def test_handle_webhook_dispatches_subscription_events(monkeypatch: pytest.MonkeyPatch) -> None:
    service = StripeService()
    service.webhook_secret = "whsec_test"
    fake_db = AsyncMock()

    event = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_123",
                "status": "active",
                "metadata": {"user_id": "user-1", "tier": "Pro"},
            }
        },
    }

    dispatch = AsyncMock()
    monkeypatch.setattr(service, "_dispatch_event", dispatch)
    monkeypatch.setattr("backend.src.services.stripe_service.stripe.Webhook.construct_event", lambda payload, sig_header, secret: event)

    result = await service.handle_webhook(payload=b"{}", signature="sig", db=fake_db)

    assert result["received"] is True
    dispatch.assert_awaited_once_with(event, fake_db)


@pytest.mark.asyncio
async def test_dispatch_event_handles_subscription_deleted(monkeypatch: pytest.MonkeyPatch) -> None:
    service = StripeService()
    fake_db = AsyncMock()

    sync_mock = AsyncMock()
    monkeypatch.setattr(service, "sync_subscription_to_tier", sync_mock)

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_456", "metadata": {"user_id": "user-2"}}},
    }

    await service._dispatch_event(event, fake_db)

    sync_mock.assert_awaited_once_with(event["data"]["object"], event_type=event["type"], db=fake_db)
