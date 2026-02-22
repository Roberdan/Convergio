"""Waitlist API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.admin import require_admin
from ..core.database import get_db_session
from ..services import waitlist_service

router = APIRouter(tags=["Waitlist"])


class WaitlistSubmitRequest(BaseModel):
    email: str
    name: str


class WaitlistRejectRequest(BaseModel):
    notes: str | None = None


@router.post("/api/v1/waitlist", status_code=status.HTTP_201_CREATED)
async def submit_waitlist(
    payload: WaitlistSubmitRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        return await waitlist_service.submit_waitlist_request(db, email=str(payload.email), name=payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/api/v1/admin/waitlist")
async def list_waitlist(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db_session),
    _: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    return await waitlist_service.list_waitlist_requests(db, status=status_filter)


@router.post("/api/v1/admin/waitlist/{waitlist_id}/approve")
async def approve_waitlist(
    waitlist_id: str,
    db: AsyncSession = Depends(get_db_session),
    admin_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        return await waitlist_service.approve_waitlist_request(
            db,
            waitlist_id=waitlist_id,
            admin_email=str(admin_user.get("email") or "admin"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/api/v1/admin/waitlist/{waitlist_id}/reject")
async def reject_waitlist(
    waitlist_id: str,
    payload: WaitlistRejectRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    try:
        return await waitlist_service.reject_waitlist_request(
            db,
            waitlist_id=waitlist_id,
            admin_email=str(admin_user.get("email") or "admin"),
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
