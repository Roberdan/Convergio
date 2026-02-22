"""Utilities for async structured logging with PII sanitization."""

import asyncio
import logging
import logging.handlers
import os
import re
import sys
from queue import Queue
from typing import Any, List

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, filter_by_level

REDACTED = "[REDACTED]"
REDACTED_EMAIL = "[REDACTED_EMAIL]"
SENSITIVE_FIELD_NAMES = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "authorization",
}
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
API_KEY_PATTERN = re.compile(r"\b(sk_(live|test)_[A-Za-z0-9]+|AIza[0-9A-Za-z\-_]{20,})\b")
BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+\b", re.IGNORECASE)

_queue_listener: logging.handlers.QueueListener | None = None

class LocalQueueHandler(logging.handlers.QueueHandler):
    """A custom QueueHandler that avoids unnecessary processing for in-process queues."""
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.

        Writes the LogRecord to the queue, handling task cancellation gracefully.
        This version removes the expensive `prepare()` call, as it's not needed
        for local, in-process queues.
        """
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.handleError(record)


def _sanitize_string(value: str) -> str:
    """Mask sensitive content from free-text log strings."""
    masked = EMAIL_PATTERN.sub(REDACTED_EMAIL, value)
    masked = API_KEY_PATTERN.sub(REDACTED, masked)
    masked = BEARER_PATTERN.sub(REDACTED, masked)
    return masked


def _sanitize_value(field_name: str | None, value: Any) -> Any:
    """Recursively sanitize values based on field names and value content."""
    normalized_name = (field_name or "").lower()
    if normalized_name in SENSITIVE_FIELD_NAMES:
        return REDACTED_EMAIL if normalized_name == "email" else REDACTED

    if isinstance(value, dict):
        return {key: _sanitize_value(str(key), inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(field_name, item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(field_name, item) for item in value)
    if isinstance(value, str):
        if normalized_name == "email":
            return REDACTED_EMAIL
        return _sanitize_string(value)
    return value


def sanitize_log_output(
    _logger: logging.Logger, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that redacts PII and secrets from event payloads."""
    return {key: _sanitize_value(str(key), value) for key, value in event_dict.items()}


def add_request_id(
    _logger: logging.Logger, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Ensure every log event carries a correlation ID."""
    context = structlog.contextvars.get_contextvars()
    event_dict["request_id"] = str(context.get("request_id", "unknown"))
    return event_dict


def _configure_structlog() -> None:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    explicit_format = os.getenv("LOG_FORMAT", "").lower()

    if explicit_format in {"json", "console"}:
        renderer = JSONRenderer() if explicit_format == "json" else ConsoleRenderer()
    else:
        renderer = JSONRenderer() if environment == "production" else ConsoleRenderer()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    structlog.configure(
        processors=[
            filter_by_level,
            structlog.contextvars.merge_contextvars,
            add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            add_request_id,
            sanitize_log_output,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def setup_async_logging() -> None:
    """
    Set up non-blocking logging by moving all existing root handlers
    to a QueueListener running in a separate thread.

    This prevents logging I/O (e.g., writing to files or the console)
    from blocking the asyncio event loop.
    """
    global _queue_listener

    _configure_structlog()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.INFO),
        force=True,
    )

    queue = Queue()
    root_logger = logging.getLogger()

    handlers: List[logging.Handler] = []

    # Create a queue handler to replace the existing handlers
    queue_handler = LocalQueueHandler(queue)

    # Remove existing handlers and store them for the listener
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handlers.append(handler)

    # Add the single queue handler to the root logger
    root_logger.addHandler(queue_handler)

    if _queue_listener is not None:
        _queue_listener.stop()

    # Create and start the listener with the original handlers
    _queue_listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    _queue_listener.start()
    logging.getLogger(__name__).info("Non-blocking asyncio logging configured.")
