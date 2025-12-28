"""
🚀 Convergio - Unified Backend Main Application
Modern FastAPI + SQLAlchemy 2.0 + Redis + AI Agents + Vector Search

Architecture: Single Python service replacing 4 microservices
- Backend (Go) → Python FastAPI
- Agents (Python) → Integrated AI orchestration  
- Vector (Go) → Integrated vector search
- Database: Shared PostgreSQL
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
# Enhanced rate limiting system
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.rate_limiting_enhanced import create_enhanced_rate_limiter, get_slowapi_limiter, ProductionRateLimitMiddleware

from .core.config_enhanced import initialize_configuration
from .core.database import init_db, close_db
from .core.redis import init_redis, close_redis
from .core.logging_utils import setup_async_logging
from .core.security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from .core.error_handling_enhanced import error_handler, handle_startup_validation
from .core.security_config import initialize_secure_defaults, validate_security_config
from .core.config_validator import ConfigValidator

# Import routers
from .api.talents import router as talents_router
from .api.project_team import router as project_team_router
from .api.agents import router as agents_router
from .api.vector import router as vector_router
from .api.health import router as health_router
from .api.user_keys import router as user_keys_router
from .api.ali_intelligence import router as ali_intelligence_router
from .api.cost_management import router as cost_management_router
from .api.analytics import router as analytics_router
from .api.workflows import router as workflows_router
from .api.agent_signatures import router as agent_signatures_router
from .api.component_serialization import router as serialization_router
from .api.agent_management import router as agent_management_router
from .api.swarm_coordination import router as swarm_coordination_router
from .api.agents_ecosystem import router as agents_ecosystem_router
from .api.admin import router as admin_router
from .api.approvals import router as approvals_router
from .api.projects import router as projects_router
from .api.system_status import router as system_status_router
from .api.telemetry import router as telemetry_router
from .api.governance import router as governance_router
from .api.pm_orchestration import router as pm_orchestration_router
from .api.realtime_endpoints import router as realtime_router
from .api.ai_settings import router as ai_settings_router

# Setup non-blocking structured logging for asyncio
setup_async_logging()
logger = structlog.get_logger()

# Rate limiting
# limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan management - startup and shutdown events"""
    
    # 🚀 STARTUP
    # Initialize secure defaults before configuration
    try:
        logger.info("🔐 Initializing secure defaults...")
        initialize_secure_defaults()
        logger.info("✅ Secure defaults initialized")
    except Exception as e:
        logger.warning(f"⚠️ Secure defaults initialization skipped: {e}")
    
    # Initialize configuration with fail-fast behavior
    settings = initialize_configuration()
    logger.info("🚀 Starting Convergio Unified Backend", version=settings.PROJECT_VERSION)
    
    # Comprehensive configuration validation
    config_validator = ConfigValidator()
    if not config_validator.validate_startup():
        logger.error("❌ Configuration validation failed - terminating startup")
        raise RuntimeError("Configuration validation failed")
    
    # Validate security configuration
    try:
        config_dict = {
            "JWT_SECRET": settings.JWT_SECRET,
            "CORS_ALLOWED_ORIGINS": ",".join(settings.cors_origins_list),
            "BASE_URL": settings.BASE_URL if hasattr(settings, 'BASE_URL') else "",
            "POSTGRES_HOST": settings.POSTGRES_HOST,
            "REDIS_HOST": settings.REDIS_HOST,
        }
        validate_security_config(config_dict, settings.ENVIRONMENT)
        logger.info("✅ Security configuration validated")
    except Exception as e:
        logger.warning(f"⚠️ Security configuration validation: {e}")
    
    # Validate required services configuration
    handle_startup_validation(["database", "redis", "ai_apis"])
    
    try:
        # Initialize database
        logger.info("📊 Initializing database connection pool...")
        async with error_handler.error_context("database", "initialization"):
            await init_db()
            logger.info("✅ Database connection pool initialized")
        # Auto-create tables in development for smoother E2E/dev experience
        try:
            if settings.ENVIRONMENT == "development" and os.getenv("SKIP_AUTO_MIGRATIONS", "false").lower() not in ("true", "1", "yes"):
                from .core.database import async_engine
                async with async_engine.begin() as conn:
                    # Create tables if not exist
                    from .core.database import Base
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("🧱 Database tables ensured (development mode)")
                # Ensure specific dev schema consistency (lightweight auto-migrations)
                from .core.database import ensure_dev_schema
                await ensure_dev_schema()
            else:
                logger.info("⏭️ Auto-migrations skipped (SKIP_AUTO_MIGRATIONS=true)")
        except Exception as _e:
            logger.warning(f"⚠️ Table auto-create skipped/failed: {_e}")
        
        # Initialize Redis with enhanced error handling
        logger.info("🚀 Initializing Redis connection pool...")  
        async with error_handler.error_context("redis", "initialization"):
            await init_redis()
            logger.info("✅ Redis connection pool initialized")
        
        # Initialize enhanced rate limiting system
        logger.info("🚦 Initializing enhanced rate limiting...")
        try:
            from .core.redis import get_redis_client
            redis_client = await get_redis_client()
            
            rate_engine, rate_middleware = create_enhanced_rate_limiter(
                redis_client, 
                enabled=settings.RATE_LIMITING_ENABLED
            )
            
            # Configure endpoint-specific limits  
            await rate_engine.configure_endpoint_limits(settings.RATE_LIMITS)
            logger.info("✅ Enhanced rate limiting initialized")
        except Exception as e:
            logger.error("❌ Rate limiting initialization failed", error=str(e))
            if settings.ENVIRONMENT == "production":
                raise
        
        # Initialize AI agent system
        logger.info("🤖 Initializing AI agent orchestration system...")
        try:
            from .agents.orchestrator import initialize_agents
            await initialize_agents()
            logger.info("✅ AI Agent System initialized successfully")
        except Exception as agent_error:
            logger.warning(f"⚠️ AI agents partially initialized: {agent_error}")
            logger.info("📈 Backend operational, agent system will retry on next startup")
        
        # Initialize streaming orchestrator system
        logger.info("🌊 Initializing streaming orchestrator system...")
        try:
            from .agents.services.streaming_orchestrator import get_streaming_orchestrator
            streaming_orchestrator = get_streaming_orchestrator()
            await streaming_orchestrator.initialize()
            logger.info("✅ Streaming Orchestrator initialized successfully")
        except Exception as streaming_error:
            logger.warning(f"⚠️ Streaming orchestrator initialization failed: {streaming_error}")
            logger.info("📈 Backend operational, streaming system will retry on demand")
        
        # Vector search integrated in API
        logger.info("🔍 Vector search engine ready")
        
        # Initialize database maintenance scheduler
        logger.info("🔧 Initializing database maintenance scheduler...")
        try:
            from .core.db_maintenance import get_db_maintenance
            db_maintenance = get_db_maintenance()
            # Schedule VACUUM ANALYZE at 3:00 AM UTC daily
            db_maintenance.schedule_maintenance(vacuum_hour=3, vacuum_minute=0)
            logger.info("✅ Database maintenance scheduler started (VACUUM at 03:00 UTC)")
        except Exception as maintenance_error:
            logger.warning(f"⚠️ Database maintenance scheduler failed: {maintenance_error}")
            logger.info("📈 Backend operational, maintenance can be scheduled manually")
        
        logger.info("✅ Convergio backend startup completed successfully")
        
    except Exception as e:
        logger.error("❌ Failed to start Convergio backend", error=str(e))
        raise
    
    yield
    
    # 🛑 SHUTDOWN
    logger.info("🛑 Shutting down Convergio backend...")
    
    try:
        # Stop database maintenance scheduler
        try:
            from .core.db_maintenance import get_db_maintenance
            db_maintenance = get_db_maintenance()
            db_maintenance.stop_maintenance()
            logger.info("✅ Database maintenance scheduler stopped")
        except Exception as e:
            logger.warning(f"⚠️ Error stopping maintenance scheduler: {e}")
        
        await close_redis()
        await close_db()
        logger.info("✅ Convergio backend shutdown completed")
    except Exception as e:
        logger.error("❌ Error during shutdown", error=str(e))

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    settings = initialize_configuration()
    
    # Create FastAPI app with lifespan management
    app = FastAPI(
        title="🚀 Convergio - Unified AI Platform",
        description="""
        **Next-Generation AI-Native Business Platform**
        
        Unified architecture combining:
        - 👥 **Talent & Resource Management** 
        - 🤖 **AI Agent Orchestration** (AutoGen 0.7.1)
        - 🔍 **Vector Search & Embeddings**
        - 📊 **Real-time Analytics & Monitoring**
        
        **Performance**: AsyncIO + Connection Pooling + Redis Caching
        **Security**: Rate limiting + CORS
        **Scalability**: Horizontal scaling + Background tasks + WebSockets
        """,
        version=settings.PROJECT_VERSION,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )
    
    # ================================
    # 🛡️ SECURITY MIDDLEWARE STACK
    # ================================
    
    # Enhanced Rate Limiting Middleware (first for security)
    # Note: Redis is initialized in lifespan startup. Middleware is attached here without blocking on Redis.
    if settings.RATE_LIMITING_ENABLED:
        try:
            from .core.redis import get_redis_client
            redis_client = get_redis_client()
            rate_engine, _ = create_enhanced_rate_limiter(redis_client, enabled=True)
            app.add_middleware(ProductionRateLimitMiddleware, rate_engine=rate_engine, enabled=True)
            # Backwards compatibility: slowapi handler
            limiter = get_slowapi_limiter()
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        except Exception as e:
            logger.warning(f"⚠️ Rate limiting middleware initialization deferred: {e}")
    
    # Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS - Must be first - Fix credentials issue
    cors_origins = settings.cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Request-ID"],
    )
    
    # Trusted hosts (production security)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts_list,
        )
    
    # Optional simple in-process rate limiting (feature-flagged)
    if os.getenv("FEATURE_RATE_LIMIT", "false").lower() in ("1", "true", "yes"):
        try:
            # conservative defaults
            app.add_middleware(RateLimitMiddleware, calls=int(os.getenv("RATE_LIMIT_CALLS", 100)), period=int(os.getenv("RATE_LIMIT_PERIOD", 60)))
            logger.info("✅ RateLimitMiddleware enabled")
        except Exception as e:
            logger.warning(f"⚠️ Could not enable RateLimitMiddleware: {e}")
    
    
    # ================================
    # 📊 MONITORING & METRICS
    # ================================
    
    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req-{asyncio.current_task().get_name()}")
        
        # Set context for structured logging
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # ================================
    # 🛣️ API ROUTES REGISTRATION
    # ================================
    
    # Health checks (public)
    app.include_router(health_router, prefix="/health", tags=["Health"])

    # AI Provider Settings (no auth required)
    app.include_router(ai_settings_router, prefix="/api/v1/settings/ai", tags=["AI Settings"])

    # Business logic APIs (no auth required)
    app.include_router(talents_router, prefix="/api/v1/talents", tags=["Talents"])
    app.include_router(project_team_router, prefix="/api/v1", tags=["Project Team"])

    # AI orchestration APIs (no auth required)
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["AI Agents"])
    
    # Ali Intelligence API (single registration)
    app.include_router(ali_intelligence_router, prefix="/api/v1/agents", tags=["Ali Intelligence"])
    
    # Agent ecosystem health monitoring
    app.include_router(agents_ecosystem_router, tags=["Agent Ecosystem"])
    
    # Admin endpoints for database maintenance
    app.include_router(admin_router, tags=["Admin"])
    
    # System status endpoints
    app.include_router(system_status_router, tags=["System"])
    
    # Vector search APIs (no auth required)
    app.include_router(vector_router, prefix="/api/v1/vector", tags=["Vector Search"])
    
    # User API Keys management (no auth required)
    app.include_router(user_keys_router, prefix="/api/v1", tags=["User Keys"])
    
    # (Removed duplicate Ali Intelligence router registration)
    
    # Cost Management & Monitoring (no auth required for real-time data)
    app.include_router(cost_management_router, prefix="/api/v1/cost-management", tags=["Cost Management"])
    
    # Analytics & Dashboard (CEO Dashboard Supreme support)
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
    
    # Approvals system 
    app.include_router(approvals_router, prefix="/api/v1/approvals", tags=["Approvals"])
    
    # Projects & Clients (Real database data)
    app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects & Clients"])
    
    # Workflows & Business Process Automation (GraphFlow) - FIX: Add proper prefix
    app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["Workflows"])
    
    # Agent Digital Signatures & Validation - FIX: Add proper prefix
    app.include_router(agent_signatures_router, prefix="/api/v1/agent-signatures", tags=["Agent Signatures"])
    
    # Component Serialization & State Management - FIX: Add proper prefix  
    app.include_router(serialization_router, prefix="/api/v1/serialization", tags=["Component Serialization"])
    
    # Agent Management System (CRUD operations for agents)
    app.include_router(agent_management_router, prefix="/api/v1/agent-management", tags=["Agent Management"])
    
    # Swarm Coordination System (Advanced agent coordination with swarm intelligence)
    app.include_router(swarm_coordination_router, prefix="/api/v1/swarm", tags=["Swarm Coordination"])
    
    # Telemetry System (Operational UX data for M4)
    app.include_router(telemetry_router, tags=["Telemetry"])
    
    # Governance System (Rate limiting, SLO monitoring, Runbooks for M5)
    app.include_router(governance_router, prefix="/api/v1/governance", tags=["Governance"])
    
    # PM Orchestration System (AI-orchestrated project management)
    app.include_router(pm_orchestration_router, tags=["PM Orchestration"])
    
    # Real-time Streaming System (WebSocket and SSE for orchestration updates)
    app.include_router(realtime_router, tags=["Real-time Streaming"])
    
    # ================================
    # 🔄 GLOBAL EXCEPTION HANDLERS
    # ================================
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler with structured logging"""
        
        logger.error(
            "🚨 Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True
        )
        
        # Don't expose internal errors in production
        if settings.ENVIRONMENT == "production":
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request.headers.get("X-Request-ID")
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "request_id": request.headers.get("X-Request-ID")
                }
            )
    
    
    # ================================
    # 🏠 ROOT ENDPOINT
    # ================================
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint with service information"""
        return {
            "service": "Convergio Unified Backend",
            "version": settings.PROJECT_VERSION,
            "build": os.getenv("BUILD_NUMBER", "dev"),
            "environment": settings.ENVIRONMENT,
            "status": "🚀 Running",
            "architecture": "FastAPI + SQLAlchemy 2.0 + Redis + AI",
            "features": [
                "👥 Talent Management", 
                "🤖 AI Agent Orchestration",
                "🔍 Vector Search Engine",
                "📊 Real-time Analytics"
            ],
            "docs": "/docs" if settings.ENVIRONMENT != "production" else None
        }
    
    logger.info("✅ FastAPI application configured successfully")
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    settings = initialize_configuration()
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=9000,  # Convergio port (no conflicts)
        reload=settings.ENVIRONMENT != "production",
        log_level="info",
        loop="asyncio",
        # Performance optimizations
        workers=1 if settings.ENVIRONMENT != "production" else 4,
        access_log=settings.ENVIRONMENT != "production",
    )