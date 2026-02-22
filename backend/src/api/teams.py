"""Team API endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import validate_session
from ..core.database import get_db_session
from ..services import team_service

logger = structlog.get_logger()
router = APIRouter(tags=["Teams"])
SESSION_COOKIE_NAME = "session"


class MemberType(str, Enum):
    # Allowed member types: human and agent
    human = "human"
    agent = "agent"


class TeamRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class TeamMemberCreateRequest(BaseModel):
    type: MemberType
    role: TeamRole = TeamRole.member
    userId: str | None = None
    agentId: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "TeamMemberCreateRequest":
        if self.type == MemberType.human and not self.userId:
            raise ValueError("userId is required when type is human")
        if self.type == MemberType.agent and not self.agentId:
            raise ValueError("agentId is required when type is agent")
        return self


class TeamMemberResponse(BaseModel):
    id: str | None = None
    teamId: str
    userId: str | None = None
    agentId: str | None = None
    role: str
    type: str


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    members: list[TeamMemberResponse] = []


async def _current_user_id(db: AsyncSession, request: Request) -> str:
    session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    if not session_data or not session_data.get("userId"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return str(session_data["userId"])


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    team = await team_service.create_team(
        db,
        owner_user_id=user_id,
        name=payload.name,
        description=payload.description,
    )
    logger.info("team.created", team_id=team.get("id"), user_id=user_id)
    return team


@router.get("/teams", response_model=list[TeamResponse])
async def list_teams(request: Request, db: AsyncSession = Depends(get_db_session)) -> list[dict[str, Any]]:
    user_id = await _current_user_id(db, request)
    teams = await team_service.list_user_teams(db, user_id=user_id)
    return [{**team, "members": []} for team in teams]


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str, request: Request, db: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    team = await team_service.get_team_with_members(db, team_id=team_id, user_id=user_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    team_id: str,
    payload: TeamMemberCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    user_id = await _current_user_id(db, request)
    try:
        member = await team_service.add_member(
            db,
            team_id=team_id,
            actor_user_id=user_id,
            member_type=payload.type.value,
            role=payload.role.value,
            user_id=payload.userId,
            agent_id=payload.agentId,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info("team.member.added", team_id=team_id, role=member.get("role"), type=member.get("type"))
    return member
