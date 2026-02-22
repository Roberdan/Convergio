"""Stripe checkout + webhook integration service."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

import stripe
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class StripeService:
    """Encapsulates Stripe checkout and webhook handlers."""

    _SUBSCRIPTION_EVENTS = {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }

    def __init__(self) -> None:
        self.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        if self.api_key:
            stripe.api_key = self.api_key

    async def create_checkout_session(
        self,
        *,
        user_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, str]:
        payload = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": user_id,
            "metadata": {"user_id": user_id, **(metadata or {})},
        }
        if customer_email:
            payload["customer_email"] = customer_email

        session = stripe.checkout.Session.create(**payload)
        return {"id": session["id"], "url": session["url"]}

    async def handle_webhook(self, payload: bytes, signature: str, db: AsyncSession) -> dict[str, Any]:
        if not signature:
            raise ValueError("Missing Stripe signature header")
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")

        event = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=self.webhook_secret)
        await self._dispatch_event(event, db)
        return {"received": True, "type": event["type"]}

    async def _dispatch_event(self, event: dict[str, Any], db: AsyncSession) -> None:
        event_type = event["type"]
        if event_type in self._SUBSCRIPTION_EVENTS:
            await self.sync_subscription_to_tier(event["data"]["object"], event_type=event_type, db=db)
            return
        logger.info("stripe_event_ignored", event_type=event_type)

    async def sync_subscription_to_tier(
        self,
        subscription: dict[str, Any],
        *,
        event_type: str,
        db: AsyncSession,
    ) -> None:
        metadata = subscription.get("metadata", {}) or {}
        user_id = metadata.get("user_id") or metadata.get("userId")
        stripe_subscription_id = subscription.get("id")
        status = "canceled" if event_type == "customer.subscription.deleted" else subscription.get("status", "active")
        requested_tier = metadata.get("tier", "Pro")
        tier_name = "Trial" if event_type == "customer.subscription.deleted" else requested_tier

        tier_id = await self._fetch_tier_id(db, tier_name)
        if not tier_id:
            tier_id = await self._fetch_tier_id(db, "Trial")

        await self._upsert_subscription(
            db=db,
            columns=await self._subscription_columns(db),
            stripe_subscription_id=stripe_subscription_id,
            user_id=user_id,
            tier_id=tier_id,
            status=status,
        )

        if user_id:
            await db.execute(
                text("UPDATE talents SET tier = :tier_name WHERE CAST(id AS TEXT) = :user_id"),
                {"tier_name": tier_name, "user_id": str(user_id)},
            )
        await db.commit()

    async def _fetch_tier_id(self, db: AsyncSession, tier_name: str) -> str | None:
        result = await db.execute(
            text('SELECT id FROM "Tier" WHERE LOWER(name) = LOWER(:tier_name) LIMIT 1'),
            {"tier_name": tier_name},
        )
        row = result.mappings().first()
        return str(row["id"]) if row else None

    async def _subscription_columns(self, db: AsyncSession) -> set[str]:
        result = await db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'Subscription'
                """
            )
        )
        return {str(row[0]) for row in result.fetchall()}

    async def _upsert_subscription(
        self,
        *,
        db: AsyncSession,
        columns: Iterable[str],
        stripe_subscription_id: str | None,
        user_id: str | None,
        tier_id: str | None,
        status: str,
    ) -> None:
        col_set = set(columns)
        params: dict[str, Any] = {"tier_id": tier_id, "status": status}
        update_parts = ['"tierId" = :tier_id', '"status" = :status']

        where = ""
        if "stripeSubscriptionId" in col_set and stripe_subscription_id:
            where = '"stripeSubscriptionId" = :stripe_subscription_id'
            params["stripe_subscription_id"] = stripe_subscription_id
        elif "userId" in col_set and user_id:
            where = '"userId" = :user_id'
            params["user_id"] = str(user_id)

        if where:
            query = f'UPDATE "Subscription" SET {", ".join(update_parts)} WHERE {where}'
            result = await db.execute(text(query), params)
            if getattr(result, "rowcount", 0):
                return

        insert_columns = ['"id"', '"tierId"', '"status"']
        insert_values = [":id", ":tier_id", ":status"]
        params["id"] = str(uuid4())

        if "stripeSubscriptionId" in col_set and stripe_subscription_id:
            insert_columns.append('"stripeSubscriptionId"')
            insert_values.append(":stripe_subscription_id")
            params["stripe_subscription_id"] = stripe_subscription_id
        if "userId" in col_set and user_id:
            insert_columns.append('"userId"')
            insert_values.append(":user_id")
            params["user_id"] = str(user_id)

        await db.execute(
            text(f'INSERT INTO "Subscription" ({", ".join(insert_columns)}) VALUES ({", ".join(insert_values)})'),
            params,
        )


stripe_service = StripeService()
