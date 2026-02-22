"""Invite API endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import validate_session
from ..core.database import get_db_session
from ..services import invite_service

router = APIRouter(tags=["Invites"])
SESSION_COOKIE_NAME = "session"


class InviteType(str, Enum):
    human = "human"
    agent = "agent"


class TeamRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class InviteCreateRequest(BaseModel):
    teamId: str
    type: InviteType
    role: TeamRole = TeamRole.member
    email: str | None = None
    agentId: str | None = None


class InviteResponse(BaseModel):
    id: str
    teamId: str
    email: str | None = None
    token: str | None = None
    role: str
    status: str
    type: str


async def _current_user_id(db: AsyncSession, request: Request) -> str:
    session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    if not session_data or not session_data.get("userId"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return str(session_data["userId"])


@router.post("/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    try:
        return await invite_service.send_invite(
            db,
            team_id=payload.teamId,
            actor_user_id=user_id,
            invite_type=payload.type.value,
            role=payload.role.value,
            email=payload.email,
            agent_id=payload.agentId,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/invites", response_model=list[InviteResponse])
async def list_invites(
    request: Request,
    team_id: str = Query(alias="teamId"),
    db: AsyncSession = Depends(get_db_session),
) -> list[dict[str, Any]]:
    user_id = await _current_user_id(db, request)
    try:
        return await invite_service.list_pending_invites(db, team_id=team_id, actor_user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/invites/{invite_id}/accept", response_model=InviteResponse)
async def accept_invite(
    invite_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    try:
        return await invite_service.accept_invite(db, invite_id=invite_id, actor_user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/invites/{invite_id}/reject", response_model=InviteResponse)
async def reject_invite(
    invite_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    try:
        return await invite_service.reject_invite(db, invite_id=invite_id, actor_user_id=user_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
