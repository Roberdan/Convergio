"""
🏥 Convergio2030 - Health Check API
Comprehensive system health monitoring
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session, check_database_health
from src.core.redis import get_redis_client
from src.agents.utils.config import get_settings

logger = structlog.get_logger()
router = APIRouter(tags=["Health"])


@router.get("/")
async def basic_health():
    """
    ❤️ Basic health check
    
    Simple endpoint to verify service is running
    """
    
    settings = get_settings()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "convergio2030-backend",
        "version": settings.app_version,
        "build": settings.build_number,
        "environment": settings.environment
    }


@router.get("/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db_session)):
    """
    🔍 Detailed health check
    
    Comprehensive system health including all dependencies
    """
    
    settings = get_settings()
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "convergio2030-backend",
        "version": settings.app_version,
        "build": settings.build_number,
        "environment": settings.environment,
        "checks": {}
    }
    
    # Check database
    try:
        db_health = await check_database_health()
        health_data["checks"]["database"] = db_health
    except Exception as e:
        logger.error("❌ Database health check failed", error=str(e))
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        health_data["checks"]["redis"] = {
            "status": "healthy",
            "connection": "active"
        }
    except Exception as e:
        logger.error("❌ Redis health check failed", error=str(e))
        health_data["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "degraded"
    
    # Overall status
    unhealthy_checks = [
        check for check in health_data["checks"].values()
        if check.get("status") != "healthy"
    ]
    
    if unhealthy_checks:
        if len(unhealthy_checks) == len(health_data["checks"]):
            health_data["status"] = "unhealthy"
        else:
            health_data["status"] = "degraded"
    
    return health_data


@router.get("/db")
async def database_health():
    """
    🗄️ Database health check
    
    Dedicated endpoint for database status monitoring
    """
    
    return await check_database_health()


@router.get("/cache")
async def cache_health():
    """
    🚀 Redis cache health check
    
    Dedicated endpoint for Redis cache status monitoring
    """
    
    try:
        redis_client = get_redis_client()
        
        # Test basic operations
        test_key = "health_check_test"
        await redis_client.set(test_key, "test_value", ex=60)
        value = await redis_client.get(test_key)
        await redis_client.delete(test_key)
        
        if value != "test_value":
            raise Exception("Redis read/write test failed")
        
        # Get Redis info
        info = await redis_client.info()
        
        return {
            "status": "healthy",
            "connection": "active",
            "version": info.get("redis_version", "unknown"),
            "memory": {
                "used": info.get("used_memory_human", "unknown"),
                "peak": info.get("used_memory_peak_human", "unknown"),
            },
            "stats": {
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        }
        
    except Exception as e:
        logger.error("❌ Redis health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/agents")
async def agents_health():
    """
    🤖 AI Agents service health check
    
    Check the integrated agents functionality
    """
    
    try:
        # TODO: Implement actual agents health check
        # For now, return basic status
        return {
            "status": "healthy",
            "message": "Agents service integrated in unified backend",
            "capabilities": [
                "autogen_agents",
                "orchestration", 
                "task_execution",
                "real_time_communication"
            ]
        }
        
    except Exception as e:
        logger.error("❌ Agents health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/vector")
async def vector_health():
    """
    🔍 Vector service health check
    
    Check the integrated vector search functionality
    """
    
    try:
        # TODO: Implement actual vector health check
        # For now, return basic status
        return {
            "status": "healthy",
            "message": "Vector service integrated in unified backend",
            "capabilities": [
                "embeddings_generation",
                "similarity_search",
                "pgvector_support",
                "document_indexing"
            ]
        }
        
    except Exception as e:
        logger.error("❌ Vector health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }