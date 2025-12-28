"""
System Status API - Check system-wide API keys and services
"""

import os
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..core.database import get_db_session
from ..core.config import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/system", tags=["System"])


@router.get("/api-status")
async def get_system_api_status() -> Dict[str, Any]:
    """
    Get system-wide API configuration status.
    Checks both .env configuration and user-provided keys.
    """
    settings = get_settings()
    
    status = {
        "openai": {
            "connected": False,
            "source": None,
            "model": None
        },
        "anthropic": {
            "connected": False,
            "source": None,
            "model": None
        },
        "perplexity": {
            "connected": False,
            "source": None,
            "model": None
        },
        "backend": {
            "connected": True,
            "version": os.environ.get("APP_VERSION", "1.0.0")
        }
    }
    
    # Check OpenAI
    if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        # Valid OpenAI keys start with sk-proj- or sk-
        
        #if settings.OPENAI_API_KEY.startswith(('sk-proj-', 'sk-')):
        status["openai"]["connected"] = True
        status["openai"]["source"] = "system"
        status["openai"]["model"] = settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else "gpt-4o-mini"
    
    # Check Anthropic  
    if hasattr(settings, 'ANTHROPIC_API_KEY') and settings.ANTHROPIC_API_KEY:
        # Valid Anthropic keys start with sk-ant-
        if settings.ANTHROPIC_API_KEY.startswith('sk-ant-'):
            status["anthropic"]["connected"] = True
            status["anthropic"]["source"] = "system"
            status["anthropic"]["model"] = settings.ANTHROPIC_MODEL if hasattr(settings, 'ANTHROPIC_MODEL') else "claude-3-opus"
    
    # Check Perplexity
    if hasattr(settings, 'PERPLEXITY_API_KEY') and settings.PERPLEXITY_API_KEY:
        # Valid Perplexity keys start with pplx-
        if settings.PERPLEXITY_API_KEY.startswith('pplx-'):
            status["perplexity"]["connected"] = True
            status["perplexity"]["source"] = "system"
            status["perplexity"]["model"] = "sonar"
    
    return status


@router.get("/health-detailed")
async def get_detailed_health(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    Get detailed system health including all services.
    """
    
    # Get API status
    api_status = await get_system_api_status(db)
    
    # Check database
    try:
        await db.execute("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False

    # Check Redis
    try:
        from ..core.redis import redis_client
        if redis_client:
            await redis_client.ping()
            redis_connected = True
        else:
            redis_connected = False
    except Exception:
        redis_connected = False
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "services": {
            "database": {
                "connected": db_connected,
                "type": "PostgreSQL"
            },
            "redis": {
                "connected": redis_connected,
                "type": "Redis"
            },
            "apis": api_status
        }
    }


# Legacy simple status for tests that just need a heartbeat
@router.get("/status")
async def simple_status() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "version": settings.app_version,
        "environment": settings.ENVIRONMENT,
        "status": "ok"
    }