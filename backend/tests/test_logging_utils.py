"""Tests for structured logging helpers with PII sanitization."""

import structlog

from core import logging_utils


def test_sanitize_log_output_redacts_sensitive_values():
    event_dict = {
        "event": "User login",
        "email": "alice@example.com",
        "password": "super-secret",
        "api_key": "sk_live_123456",
        "nested": {"token": "Bearer abc123", "notes": "contact me at bob@company.com"},
    }

    sanitized = logging_utils.sanitize_log_output(None, "info", event_dict)

    assert sanitized["email"] == "[REDACTED_EMAIL]"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["notes"] == "contact me at [REDACTED_EMAIL]"


def test_add_request_id_uses_contextvars_value():
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="req-123")

    enriched = logging_utils.add_request_id(None, "info", {"event": "hello"})

    assert enriched["request_id"] == "req-123"


def test_add_request_id_defaults_to_unknown_when_missing():
    structlog.contextvars.clear_contextvars()

    enriched = logging_utils.add_request_id(None, "info", {"event": "hello"})

    assert enriched["request_id"] == "unknown"
