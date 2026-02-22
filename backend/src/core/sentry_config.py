"""Sentry configuration for backend error tracking."""

from __future__ import annotations

import os
import re
from copy import deepcopy
from typing import Any

try:
    import sentry_sdk
except Exception:  # pragma: no cover - optional dependency fallback
    sentry_sdk = None


_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SENSITIVE_KEYS = {"email", "password"}


def _sanitize_string(value: str) -> str:
    """Redact email addresses from string values."""
    return _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)


def _sanitize_value(value: Any) -> Any:
    """Recursively sanitize breadcrumb values."""
    if isinstance(value, str):
        return _sanitize_string(value)
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, nested_value in value.items():
            if any(sensitive in key.lower() for sensitive in _SENSITIVE_KEYS):
                continue
            sanitized[key] = _sanitize_value(nested_value)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def before_breadcrumb(breadcrumb: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitize breadcrumb data before sending to Sentry."""
    del hint  # kept for sentry callback signature compatibility

    sanitized = deepcopy(breadcrumb)

    message = sanitized.get("message")
    if isinstance(message, str):
        sanitized["message"] = _sanitize_string(message)

    data = sanitized.get("data")
    if isinstance(data, dict):
        sanitized["data"] = _sanitize_value(data)

    return sanitized


def init_sentry() -> None:
    """Initialize Sentry using environment-driven settings."""
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn or sentry_sdk is None:
        return

    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        send_default_pii=False,
        before_breadcrumb=before_breadcrumb,
    )
