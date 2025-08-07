"""
🏥 Convergio - Health Check API
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
from src.core.config import get_settings

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
        "service": "convergio-backend",
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
        "service": "convergio-backend",
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
        # Implement actual agents health check
        from src.agents.orchestrator import get_agent_orchestrator
        from src.agents.services.agent_loader import DynamicAgentLoader
        
        try:
            orchestrator = await get_agent_orchestrator()
            loader = DynamicAgentLoader("src/agents/definitions")
            agents_metadata = loader.scan_and_load_agents()
            
            agents_count = len(agents_metadata)
            agents_healthy = agents_count > 0
            
            return {
                "status": "healthy" if agents_healthy else "degraded",
                "message": f"Agents service operational with {agents_count} agents loaded",
                "agents_count": agents_count,
                "orchestrator_ready": True,
                "capabilities": [
                    "autogen_agents",
                    "orchestration", 
                    "task_execution",
                    "real_time_communication"
                ]
            }
            
        except Exception as orchestrator_error:
            logger.warning(f"⚠️ Orchestrator initialization failed: {orchestrator_error}")
            return {
                "status": "degraded",
                "message": "Agents service available but orchestrator not ready",
                "agents_count": 0,
                "orchestrator_ready": False,
                "error": str(orchestrator_error)
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
        # Implement actual vector health check
        from src.core.database import get_db_session
        from src.models.document import Document
        
        try:
            # Test database connection and vector extension
            async for db in get_db_session():
                # Check if we can query documents table
                total_docs = await Document.count_total(db)
                
                # Test vector capabilities (if any documents exist)
                vector_ready = True
                if total_docs > 0:
                    try:
                        # Test a simple vector query
                        sample_doc = await Document.get_first(db)
                        if sample_doc and hasattr(sample_doc, 'embeddings'):
                            vector_ready = sample_doc.embeddings is not None
                    except:
                        vector_ready = False
                
                return {
                    "status": "healthy" if vector_ready else "degraded",
                    "message": f"Vector service operational - {total_docs} documents indexed",
                    "documents_count": total_docs,
                    "vector_extension": "pgvector" if vector_ready else "unavailable",
                    "capabilities": [
                        "embeddings_generation",
                        "similarity_search",
                        "pgvector_support",
                        "document_indexing"
                    ]
                }
                break  # Only need first session
            
        except Exception as db_error:
            logger.warning(f"⚠️ Database connection failed: {db_error}")
            return {
                "status": "degraded",
                "message": "Vector service available but database not ready",
                "documents_count": 0,
                "vector_extension": "unavailable",
                "error": str(db_error)
            }
        
    except Exception as e:
        logger.error("❌ Vector health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }