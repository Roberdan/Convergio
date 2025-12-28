"""
🏥 Convergio - Health Check API
Comprehensive system health monitoring
"""

import asyncio
from datetime import datetime

import structlog
from fastapi import APIRouter

from ..core.database import check_database_health
from ..core.redis import get_redis_client
from ..core.config import get_settings
from ..core.monitoring import health_checker

logger = structlog.get_logger()
router = APIRouter(tags=["Health"])


@router.get("/")
@router.get("")
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
async def detailed_health():
    """
    🔍 Detailed health check
    
    Comprehensive system health including all dependencies using enhanced monitoring
    """
    system_health = await health_checker.check_all_health()
    return health_checker.get_health_summary(system_health)


@router.get("/comprehensive")
async def comprehensive_health():
    """
    🏥 Comprehensive health check
    
    Full system health check with detailed component information
    """
    system_health = await health_checker.check_all_health()
    
    # Convert to serializable format
    return {
        "overall_status": system_health.overall_status.value,
        "timestamp": system_health.timestamp.isoformat(),
        "uptime_seconds": system_health.uptime_seconds,
        "checks": [
            {
                "name": check.name,
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "timestamp": check.timestamp.isoformat(),
                "details": check.details,
                "error": check.error
            } for check in system_health.checks
        ]
    }


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
        
        # Test basic operations (best-effort for no-op client)
        test_key = "health_check_test"
        try:
            await redis_client.set(test_key, "test_value", ex=60)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
        except Exception:
            value = None
        
        # Get Redis info if available
        try:
            info = await redis_client.info()
        except Exception:
            info = {}
        
        status = "healthy" if value == "test_value" or info != {} else "degraded"
        return {
            "status": status,
            "connection": "active" if status == "healthy" else "limited",
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
        from ..agents.orchestrator import get_agent_orchestrator
        from ..agents.services.agent_loader import DynamicAgentLoader
        
        try:
            await get_agent_orchestrator()
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
        from ..core.database import get_async_session
        from sqlalchemy import text
        
        try:
            # Test database connection and vector extension
            async with get_async_session() as db:
                # Check if pgvector extension is available
                try:
                    result = await db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
                    vector_extension_exists = result.scalar()
                except Exception:
                    vector_extension_exists = False
                
                # Check if we can create/query vector operations
                vector_ready = vector_extension_exists
                if vector_extension_exists:
                    try:
                        # Test basic vector operations
                        await db.execute(text("SELECT '[1,2,3]'::vector"))
                        vector_ready = True
                    except Exception:
                        vector_ready = False
                
                return {
                    "status": "healthy" if vector_ready else "degraded",
                    "message": f"Vector service operational - pgvector {'enabled' if vector_extension_exists else 'disabled'}",
                    "vector_extension": "pgvector" if vector_extension_exists else "unavailable",
                    "vector_operations": "functional" if vector_ready else "limited",
                    "capabilities": [
                        "embeddings_generation",
                        "similarity_search", 
                        "pgvector_support" if vector_extension_exists else "basic_storage",
                        "document_indexing"
                    ]
                }
            
        except Exception as db_error:
            logger.warning(f"⚠️ Database connection failed: {db_error}")
            return {
                "status": "degraded",
                "message": "Vector service available but database not ready",
                "vector_extension": "unavailable",
                "error": str(db_error)
            }
        
    except Exception as e:
        logger.error("❌ Vector health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/ai-services")
async def ai_services_health():
    """
    🤖 AI Services health check
    
    Check connectivity to external AI APIs
    """
    import os
    
    services = {}
    overall_status = "healthy"
    
    # Check OpenAI
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and not openai_key.startswith("sk-..."):  # Not placeholder
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_key)
            models = await client.models.list()
            services["openai"] = {
                "status": "healthy",
                "available_models": len(models.data) if models else 0,
                "connection": "active"
            }
        else:
            services["openai"] = {
                "status": "disabled",
                "message": "No valid API key configured",
                "connection": "none"
            }
    except Exception as e:
        services["openai"] = {
            "status": "unhealthy", 
            "error": str(e),
            "connection": "failed"
        }
        overall_status = "degraded"
    
    # Check Anthropic
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")  
        if anthropic_key and not anthropic_key.startswith("sk-ant-..."):  # Not placeholder
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=anthropic_key)
            # Test minimal request
            await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            services["anthropic"] = {
                "status": "healthy",
                "model": "claude-3-haiku-20240307",
                "connection": "active"
            }
        else:
            services["anthropic"] = {
                "status": "disabled",
                "message": "No valid API key configured", 
                "connection": "none"
            }
    except Exception as e:
        services["anthropic"] = {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }
        overall_status = "degraded"
    
    # Check if at least one AI service is available
    healthy_services = [s for s in services.values() if s.get("status") == "healthy"]
    if not healthy_services:
        if any(s.get("status") == "disabled" for s in services.values()):
            overall_status = "disabled"  # All services disabled (no keys)
        else:
            overall_status = "unhealthy"  # Services configured but failing
    
    return {
        "status": overall_status,
        "services": services,
        "healthy_count": len(healthy_services),
        "total_count": len(services)
    }


@router.get("/system")
async def system_health():
    """
    🌐 Complete system health check
    
    Comprehensive check of all system components
    """
    
    health_checks = {}
    start_time = datetime.utcnow()
    
    # Run all health checks concurrently
    tasks = {
        "database": asyncio.create_task(database_health()),
        "cache": asyncio.create_task(cache_health()),
        "agents": asyncio.create_task(agents_health()),
        "vector": asyncio.create_task(vector_health()),
        "ai_services": asyncio.create_task(ai_services_health()),
    }
    
    # Execute all checks concurrently
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for (service_name, _), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            logger.error(f"❌ {service_name} health check failed", error=str(result))
            health_checks[service_name] = {
                "status": "unhealthy",
                "error": str(result),
            }
        else:
            health_checks[service_name] = result
    
    # Calculate overall system status
    status_counts = {}
    for check in health_checks.values():
        status = check.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Determine overall status
    if status_counts.get("unhealthy", 0) > 0:
        if status_counts.get("healthy", 0) > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
    elif status_counts.get("degraded", 0) > 0:
        overall_status = "degraded"
    elif status_counts.get("disabled", 0) == len(health_checks):
        overall_status = "minimal"  # All services disabled
    else:
        overall_status = "healthy"
    
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    return {
        "status": overall_status,
        "timestamp": end_time.isoformat(),
        "duration_seconds": duration,
        "checks": health_checks,
        "summary": {
            "healthy": status_counts.get("healthy", 0),
            "degraded": status_counts.get("degraded", 0), 
            "unhealthy": status_counts.get("unhealthy", 0),
            "disabled": status_counts.get("disabled", 0),
            "total": len(health_checks)
        }
    }


@router.get("/startup-verification")
async def startup_verification():
    """
    🚀 Startup verification check
    
    Verify all services required for startup are healthy
    """
    from ..core.error_handling_enhanced import validate_service_connectivity
    
    try:
        # Run connectivity validation
        connectivity_results = await validate_service_connectivity()
        
        # Check critical services
        critical_services = ["database", "redis"]
        critical_status = all(connectivity_results.get(service, False) for service in critical_services)
        
        # Get AI services status
        ai_status = await ai_services_health()
        ai_available = ai_status["status"] in ["healthy", "degraded"]
        
        overall_healthy = critical_status and ai_available
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "critical_services": {
                service: connectivity_results.get(service, False) 
                for service in critical_services
            },
            "ai_services": {
                "status": ai_status["status"],
                "healthy_count": ai_status["healthy_count"]
            },
            "startup_ready": overall_healthy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("❌ Startup verification failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "startup_ready": False,
            "timestamp": datetime.utcnow().isoformat()
        }