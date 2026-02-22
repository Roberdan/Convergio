"""
Security and CORS middleware helpers.

This module centralizes:
- CORS whitelist parsing from ALLOWED_ORIGINS env var
- strict production validation (no wildcard origins)
- nonce-based CSP generation
- baseline security headers
"""

from __future__ import annotations

import secrets
from typing import Callable

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware


def get_allowed_origins(environment: str, allowed_origins_env: str | None = None) -> list[str]:
    """Build CORS origin whitelist from comma-separated ALLOWED_ORIGINS."""
    raw_origins = allowed_origins_env or "http://localhost:3000,http://localhost:5173"
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if environment == "production" and "*" in origins:
        raise ValueError("Wildcard CORS origin is not allowed in production")

    return origins


def build_csp_header(nonce: str, report_uri: str) -> str:
    """Build a strict CSP header with nonce and strict-dynamic."""
    return (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; "
        "style-src 'self'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https: wss:; "
        f"report-uri {report_uri}"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers and nonce-based CSP to every response."""

    def __init__(self, app, csp_report_uri: str = "/api/v1/security/csp-report"):
        super().__init__(app)
        self.csp_report_uri = csp_report_uri

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = build_csp_header(
            nonce=nonce,
            report_uri=self.csp_report_uri,
        )
        response.headers["X-CSP-Nonce"] = nonce

        return response
