"""Session-based authentication endpoints (cookie + DB session table)."""

from __future__ import annotations

import os
import secrets
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import create_session, destroy_session, validate_session
from ..core.database import get_db_session
from ..core.password import hash_password, verify_password

logger = structlog.get_logger()
router = APIRouter(tags=["Auth"])

SESSION_COOKIE_NAME = "session"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7
RESET_TOKEN_TTL_MINUTES = 30
CHANGE_PASSWORD_WINDOW_SECONDS = 15 * 60
CHANGE_PASSWORD_MAX_ATTEMPTS = 3

_CHANGE_PASSWORD_ATTEMPTS: dict[str, deque[datetime]] = defaultdict(deque)
_PASSWORD_RESET_TOKENS: dict[str, dict[str, Any]] = {}
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class AuthUserResponse(BaseModel):
    id: int
    email: str
    tier: str | None = None

def _set_session_cookie(response: Response, signed_cookie: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=signed_cookie,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE,
        path="/",
    )
def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")

async def _fetch_user_by_email(db: AsyncSession, email: str) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
            SELECT id, email, password_hash, tier
            FROM talents
            WHERE email = :email AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"email": email},
    )
    return result.mappings().first()
async def _fetch_user_by_id(db: AsyncSession, user_id: str | int) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
            SELECT id, email, password_hash, tier
            FROM talents
            WHERE id = :user_id AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"user_id": int(user_id)},
    )
    return result.mappings().first()
async def _send_reset_email_via_resend(email: str, token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.info("resend_api_key_missing_skip_email", email=email)
        return

    base_url = os.getenv("APP_BASE_URL", "http://localhost:4000")
    reset_link = f"{base_url}/reset-password?token={token}"
    payload = {
        "from": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
        "to": [email],
        "subject": "Reset your password",
        "html": f"<p>Use this link to reset your password: <a href='{reset_link}'>{reset_link}</a></p>",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        if response.status_code >= 400:
            logger.warning("resend_email_failed", status_code=response.status_code, body=response.text)
def _check_change_password_rate_limit(user_key: str) -> None:
    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=CHANGE_PASSWORD_WINDOW_SECONDS)
    attempts = _CHANGE_PASSWORD_ATTEMPTS[user_key]

    while attempts and attempts[0] < window_start:
        attempts.popleft()

    if len(attempts) >= CHANGE_PASSWORD_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts")
    attempts.append(now)
@router.post("/login", response_model=AuthUserResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db_session)) -> AuthUserResponse:
    user = await _fetch_user_by_email(db, payload.email)
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    signed_cookie = await create_session(db, user_id=str(user["id"]))
    _set_session_cookie(response, signed_cookie)
    return AuthUserResponse(id=user["id"], email=user["email"], tier=user.get("tier"))
@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    await destroy_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    _clear_session_cookie(response)
    return {"message": "Logged out"}
@router.post("/register", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db_session)) -> AuthUserResponse:
    existing = await _fetch_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    first_name, _, last_name = (payload.full_name or "").partition(" ")
    password_hash = hash_password(payload.password)

    created = await db.execute(
        text(
            """
            INSERT INTO talents (email, first_name, last_name, password_hash, tier)
            VALUES (:email, :first_name, :last_name, :password_hash, :tier)
            RETURNING id
            """
        ),
        {
            "email": payload.email,
            "first_name": first_name or None,
            "last_name": last_name or None,
            "password_hash": password_hash,
            "tier": "Trial",
        },
    )
    created_row = created.mappings().first()
    user_id = int(created_row["id"])
    await db.commit()

    signed_cookie = await create_session(db, user_id=str(user_id))
    _set_session_cookie(response, signed_cookie)
    return AuthUserResponse(id=user_id, email=str(payload.email), tier="Trial")
@router.post("/change-password")
async def change_password(payload: ChangePasswordRequest, request: Request, db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    if not session_data or not session_data.get("userId"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user_id = str(session_data["userId"])
    _check_change_password_rate_limit(user_id)

    user = await _fetch_user_by_id(db, user_id)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(payload.old_password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

    await db.execute(
        text("UPDATE talents SET password_hash = :password_hash WHERE id = :user_id"),
        {"password_hash": hash_password(payload.new_password), "user_id": int(user_id)},
    )
    await db.commit()
    return {"message": "Password updated"}
@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    user = await _fetch_user_by_email(db, payload.email)
    if user:
        token = secrets.token_urlsafe(32)
        _PASSWORD_RESET_TOKENS[token] = {
            "user_id": str(user["id"]),
            "expires_at": datetime.now(UTC) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
        }
        await _send_reset_email_via_resend(str(payload.email), token)
    return {"message": "If the email exists, a reset link has been sent"}
@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    token_data = _PASSWORD_RESET_TOKENS.get(payload.token)
    if not token_data or token_data["expires_at"] <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    await db.execute(
        text("UPDATE talents SET password_hash = :password_hash WHERE id = :user_id"),
        {"password_hash": hash_password(payload.new_password), "user_id": int(token_data["user_id"])},
    )
    await db.commit()
    _PASSWORD_RESET_TOKENS.pop(payload.token, None)
    return {"message": "Password reset successful"}
@router.get("/me", response_model=AuthUserResponse)
async def me(request: Request, db: AsyncSession = Depends(get_db_session)) -> AuthUserResponse:
    session_data = await validate_session(db, request.cookies.get(SESSION_COOKIE_NAME))
    if not session_data or not session_data.get("userId"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = await _fetch_user_by_id(db, session_data["userId"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return AuthUserResponse(id=int(user["id"]), email=str(user["email"]), tier=user.get("tier"))
