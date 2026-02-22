from __future__ import annotations

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from backend.src.core.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    generate_csrf_token,
    set_csrf_cookie,
    validate_csrf,
)
from backend.src.core import rate_limiting as rl


def _build_request(method: str, headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": "/api/v1/test",
            "headers": headers or [],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
        }
    )


def test_generate_csrf_token_returns_non_empty_unique_tokens() -> None:
    token_a = generate_csrf_token()
    token_b = generate_csrf_token()

    assert token_a
    assert token_b
    assert token_a != token_b


def test_set_csrf_cookie_writes_cookie_header() -> None:
    response = Response()
    token = generate_csrf_token()

    set_csrf_cookie(response, token)

    set_cookie_headers = response.headers.getlist("set-cookie")
    assert any(CSRF_COOKIE_NAME in header for header in set_cookie_headers)


def test_validate_csrf_accepts_safe_http_methods_without_headers() -> None:
    request = _build_request("GET")
    validate_csrf(request)


def test_validate_csrf_rejects_missing_header_for_mutation() -> None:
    request = _build_request("POST", headers=[(b"cookie", b"csrf_token=abc123")])

    with pytest.raises(HTTPException) as exc:
        validate_csrf(request)

    assert exc.value.status_code == 403


def test_validate_csrf_accepts_matching_cookie_and_header_for_mutation() -> None:
    request = _build_request(
        "PATCH",
        headers=[(b"cookie", b"csrf_token=csrf123"), (b"x-csrf-token", b"csrf123")],
    )

    validate_csrf(request)


def test_rate_limit_profiles_include_expected_defaults() -> None:
    assert rl.RATE_LIMIT_PROFILES["login"] == (5, 15 * 60)
    assert rl.RATE_LIMIT_PROFILES["register"] == (3, 60 * 60)
    assert rl.RATE_LIMIT_PROFILES["api_general"] == (60, 60)
    assert rl.RATE_LIMIT_PROFILES["admin_mutations"] == (30, 60)
    assert rl.RATE_LIMIT_PROFILES["admin_destructive"] == (5, 60 * 60)


@pytest.mark.asyncio
async def test_rate_limit_decorator_enforces_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    rl.reset_rate_limit_state()

    @rl.rate_limit(max_requests=2, window_seconds=60)
    async def limited_handler(request: Request) -> dict[str, bool]:
        return {"ok": True}

    request = _build_request("POST")

    assert await limited_handler(request) == {"ok": True}
    assert await limited_handler(request) == {"ok": True}
    with pytest.raises(HTTPException) as exc:
        await limited_handler(request)

    assert exc.value.status_code == 429
