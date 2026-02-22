"""CSRF protection helpers for session-based authentication flows."""

from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Request, Response, status

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, csrf_token: str) -> None:
    """Set CSRF token in a dedicated, JavaScript-readable cookie."""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax",
        path="/",
    )


def ensure_csrf_cookie(request: Request, response: Response) -> str:
    """Return existing token from cookie or create one when missing."""
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if token:
        return token

    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return token


def validate_csrf(request: Request) -> None:
    """Validate CSRF cookie/header pair for mutating HTTP methods."""
    if request.method.upper() in CSRF_SAFE_METHODS:
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if not cookie_token or not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing CSRF token",
        )

    if not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
