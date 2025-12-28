"""
📝 Convergio - Structured Logging Configuration
"""

import logging
import sys

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, filter_by_level
from structlog.dev import ConsoleRenderer

from .config import get_settings

# Define known chatty third-party loggers used in the project
openai_logger = logging.getLogger("openai")
autogen_logger = logging.getLogger("autogen")
httpx_logger = logging.getLogger("httpx")


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
            ConsoleRenderer() if settings.LOG_FORMAT == "console" else JSONRenderer(),
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
    
    # 🔇 REDUCE VERBOSE LOGGING FOR PRODUCTION
    # Set higher log levels for noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("autogen").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Create detailed conversation handler
    conversation_handler = logging.StreamHandler(sys.stdout)
    conversation_handler.setLevel(logging.DEBUG)
    conversation_formatter = logging.Formatter(
        '🤖 %(name)s [%(levelname)s] %(asctime)s - %(message)s'
    )
    conversation_handler.setFormatter(conversation_formatter)
    
    # Add handlers to AI loggers
    for ai_logger in [openai_logger, autogen_logger, httpx_logger]:
        if not ai_logger.handlers:  # Avoid duplicate handlers
            ai_logger.addHandler(conversation_handler)
            ai_logger.propagate = False  # Prevent duplicate messages
    
    # Disable noisy loggers in production (but keep AI logging)
    if settings.ENVIRONMENT == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    else:
        # In development, ensure all AI conversation details are logged
        logging.getLogger("openai._base_client").setLevel(logging.DEBUG)
        logging.getLogger("autogen_core").setLevel(logging.DEBUG)
        logging.getLogger("autogen_ext").setLevel(logging.DEBUG)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get structured logger"""
    return structlog.get_logger(name)