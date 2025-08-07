"""
📝 Convergio - Structured Logging Configuration
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, filter_by_level

from src.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging with JSON output"""
    
    settings = get_settings()
    
    # Ensure logs directory exists
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            filter_by_level,  # Filter by log level
            add_log_level,    # Add log level to event dict
            structlog.processors.TimeStamper(fmt="iso"),  # ISO timestamp
            structlog.dev.ConsoleRenderer() if settings.LOG_FORMAT == "console" else JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )
    
    # Disable noisy loggers in production
    if settings.ENVIRONMENT == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get structured logger"""
    return structlog.get_logger(name)