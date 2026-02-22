from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request

from backend.src.core.admin import require_admin


class _FakeResult:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def mappings(self) -> "_FakeResult":
        return self

    def first(self) -> dict | None:
        return self._row


def _request_with_cookie(cookie: str | None) -> Request:
    headers = []
    if cookie is not None:
        headers = [(b"cookie", f"session={cookie}".encode())]
    return Request({"type": "http", "headers": headers})


@pytest.mark.asyncio
async def test_require_admin_allows_admin_role(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.core import admin

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_FakeResult({"id": 1, "email": "admin@test.com", "role": "ADMIN"}))
    monkeypatch.setattr(admin, "validate_session", AsyncMock(return_value={"userId": "1"}))

    result = await require_admin(_request_with_cookie("signed"), db)

    assert result["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.core import admin

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_FakeResult({"id": 2, "email": "user@test.com", "role": "MEMBER"}))
    monkeypatch.setattr(admin, "validate_session", AsyncMock(return_value={"userId": "2"}))

    with pytest.raises(HTTPException) as exc:
        await require_admin(_request_with_cookie("signed"), db)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_rejects_missing_session(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.src.core import admin

    db = AsyncMock()
    monkeypatch.setattr(admin, "validate_session", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc:
        await require_admin(_request_with_cookie(None), db)

    assert exc.value.status_code == 401
