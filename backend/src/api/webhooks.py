"""Webhook endpoints."""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..services.stripe_service import stripe_service

router = APIRouter(tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db_session)) -> dict:
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()
    try:
        return await stripe_service.handle_webhook(payload=payload, signature=signature, db=db)
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
