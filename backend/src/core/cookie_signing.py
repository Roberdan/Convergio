"""Cookie signing utilities using HMAC-SHA256."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

try:
    import structlog
except ImportError:  # pragma: no cover
    structlog = None

if structlog:
    logger = structlog.get_logger()
else:  # pragma: no cover
    import logging

    logger = logging.getLogger(__name__)


def _get_secret_key() -> bytes:
    """Load and validate secret key from environment."""
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        logger.error("Missing SECRET_KEY for cookie signing")
        raise ValueError("SECRET_KEY is required for cookie signing")
    return secret_key.encode("utf-8")


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


def sign_cookie(value: str) -> str:
    """Sign a cookie value with HMAC-SHA256 and return compact token."""
    payload = _urlsafe_b64encode(value.encode("utf-8"))
    signature = hmac.new(
        _get_secret_key(),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return f"{payload}.{_urlsafe_b64encode(signature)}"


def verify_cookie(signed_value: str) -> str | None:
    """Verify signed cookie and return original value if valid."""
    try:
        payload, provided_signature = signed_value.split(".", maxsplit=1)
    except ValueError:
        logger.warning("Invalid cookie format")
        return None

    expected_signature = hmac.new(
        _get_secret_key(),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    expected_encoded = _urlsafe_b64encode(expected_signature)

    if not hmac.compare_digest(expected_encoded, provided_signature):
        logger.warning("Cookie signature verification failed")
        return None

    try:
        return _urlsafe_b64decode(payload).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        logger.warning("Unable to decode cookie payload")
        return None
