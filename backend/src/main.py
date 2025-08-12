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
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
# Rate limiting temporarily disabled - slowapi not installed
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.errors import RateLimitExceeded
# from slowapi.util import get_remote_address

from src.core.config import get_settings
from src.core.database import init_db, close_db
from src.core.redis import init_redis, close_redis
from src.core.logging import setup_logging
from src.core.security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware

# Import routers
from src.api.talents import router as talents_router
from src.api.agents import router as agents_router
from src.api.vector import router as vector_router
from src.api.health import router as health_router
from src.api.user_keys import router as user_keys_router
from src.api.ali_intelligence import router as ali_intelligence_router
from src.api.cost_management import router as cost_management_router
from src.api.analytics import router as analytics_router
from src.api.workflows import router as workflows_router
from src.api.agent_signatures import router as agent_signatures_router
from src.api.component_serialization import router as serialization_router
from src.api.agent_management import router as agent_management_router
from src.api.swarm_coordination import router as swarm_coordination_router
from src.api.agents_ecosystem import router as agents_ecosystem_router
from src.api.admin import router as admin_router

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

# Rate limiting
# limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan management - startup and shutdown events"""
    
    # 🚀 STARTUP
    logger.info("🚀 Starting Convergio Unified Backend", version=get_settings().app_version)
    
    try:
        # Initialize database
        logger.info("📊 Initializing database connection pool...")
        await init_db()
        # Auto-create tables in development for smoother E2E/dev experience
        try:
            if get_settings().ENVIRONMENT == "development":
                from sqlalchemy import text as _sql_text
                from src.core.database import async_engine
                async with async_engine.begin() as conn:
                    # Create tables if not exist
                    from src.core.database import Base
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("🧱 Database tables ensured (development mode)")
                # Ensure specific dev schema consistency (lightweight auto-migrations)
                from src.core.database import ensure_dev_schema
                await ensure_dev_schema()
        except Exception as _e:
            logger.warning(f"⚠️ Table auto-create skipped/failed: {_e}")
        
        # Initialize Redis
        logger.info("🚀 Initializing Redis connection pool...")  
        await init_redis()
        
        # Initialize AI agent system
        logger.info("🤖 Initializing AI agent orchestration system...")
        try:
            from src.agents.orchestrator import initialize_agents
            await initialize_agents()
            logger.info("✅ AI Agent System initialized successfully")
        except Exception as agent_error:
            logger.warning(f"⚠️ AI agents partially initialized: {agent_error}")
            logger.info("📈 Backend operational, agent system will retry on next startup")
        
        # Initialize streaming orchestrator system
        logger.info("🌊 Initializing streaming orchestrator system...")
        try:
            from src.agents.services.streaming_orchestrator import get_streaming_orchestrator
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
            from src.core.db_maintenance import get_db_maintenance
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
            from src.core.db_maintenance import get_db_maintenance
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
    
    settings = get_settings()
    
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
    version=settings.app_version,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )
    
    # ================================
    # 🛡️ SECURITY MIDDLEWARE STACK
    # ================================
    
    # Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # CORS - Must be first - Fix credentials issue
    cors_origins = settings.cors_origins_list + ["http://localhost:4001", "http://127.0.0.1:4001"]
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
    
    # Rate limiting - Temporarily disabled
    # # Configuration: 100 requests per 60 seconds per IP
    # app.state.limiter = limiter
    # app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    
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
    
    # Business logic APIs (no auth required)
    app.include_router(talents_router, prefix="/api/v1/talents", tags=["Talents"])
    
    # AI orchestration APIs (no auth required)
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["AI Agents"])
    
    # Agent ecosystem health monitoring
    app.include_router(agents_ecosystem_router, tags=["Agent Ecosystem"])
    
    # Admin endpoints for database maintenance
    app.include_router(admin_router, tags=["Admin"])
    
    # Vector search APIs (no auth required)
    app.include_router(vector_router, prefix="/api/v1/vector", tags=["Vector Search"])
    
    # User API Keys management (no auth required)
    app.include_router(user_keys_router, prefix="/api/v1", tags=["User Keys"])
    
    # Ali Intelligence System (CEO assistant)
    app.include_router(ali_intelligence_router, prefix="/api/v1", tags=["Ali Intelligence"])
    
    # Cost Management & Monitoring (no auth required for real-time data)
    app.include_router(cost_management_router, prefix="/api/v1/cost-management", tags=["Cost Management"])
    
    # Analytics & Dashboard (CEO Dashboard Supreme support)
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
    
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
            "version": settings.app_version,
            "build": settings.build_number,
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
    
    settings = get_settings()
    
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