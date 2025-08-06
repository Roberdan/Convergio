"""
🗄️ Convergio2030 - Database Management
Async SQLAlchemy 2.0 + PostgreSQL with connection pooling
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy import event, pool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from src.core.config import get_settings

logger = structlog.get_logger()

# Global database components
async_engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


def create_database_engine() -> AsyncEngine:
    """Create async database engine with optimized settings"""
    
    settings = get_settings()
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        # Connection pool settings
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_POOL_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Validate connections before use
        poolclass=AsyncAdaptedQueuePool,
        
        # Performance settings
        echo=settings.ENVIRONMENT == "development",  # SQL logging in dev
        echo_pool=settings.DEBUG,  # Pool logging for debugging
        future=True,  # Use SQLAlchemy 2.0 style
        
        # Async settings
        connect_args={
            "command_timeout": 30,
            "server_settings": {
                "jit": "off",  # Disable JIT for better performance
                "application_name": "convergio2030_backend",
            },
        },
    )
    
    logger.info(
        "📊 Database engine created",
        url=settings.DATABASE_URL.split("@")[1],  # Hide credentials
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_POOL_OVERFLOW,
    )
    
    return engine


async def init_db() -> None:
    """Initialize database connection and session factory"""
    
    global async_engine, async_session_factory
    
    try:
        # Create async engine
        async_engine = create_database_engine()
        
        # Create session factory
        async_session_factory = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Keep objects usable after commit
            autoflush=True,  # Auto-flush before queries
            autocommit=False,  # Explicit transaction control
        )
        
        # Test connection
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error("❌ Failed to initialize database", error=str(e))
        raise


async def close_db() -> None:
    """Close database connections"""
    
    global async_engine
    
    if async_engine:
        try:
            await async_engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error("❌ Error closing database", error=str(e))
        finally:
            async_engine = None


def get_async_session_factory() -> async_sessionmaker:
    """Get async session factory"""
    
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with automatic cleanup"""
    
    session_factory = get_async_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency for FastAPI route injection
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection"""
    
    async with get_async_session() as session:
        yield session


# Database event listeners for monitoring
# @event.listens_for(async_engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     """Set database connection parameters"""
#     
#     if hasattr(dbapi_connection, "set_isolation_level"):
#         # PostgreSQL specific settings
#         pass


# @event.listens_for(async_engine, "checkout")
# def receive_checkout(dbapi_connection, connection_record, connection_proxy):
#     """Monitor connection checkout"""
#     
#     logger.debug("📊 Database connection checked out")


# @event.listens_for(async_engine, "checkin")
# def receive_checkin(dbapi_connection, connection_record):
#     """Monitor connection checkin"""
#     
#     logger.debug("📊 Database connection checked in")


# Utility functions for database operations
async def execute_query(query: str, params: dict = None) -> list:
    """Execute raw SQL query"""
    
    async with get_async_session() as session:
        result = await session.execute(query, params or {})
        return result.fetchall()


async def check_database_health() -> dict:
    """Check database health and connection pool status"""
    
    try:
        async with get_async_session() as session:
            # Test query
            result = await session.execute(text("SELECT version(), current_database(), current_user"))
            db_info = result.fetchone()
            
            # Get connection pool stats
            pool = async_engine.pool
            
            return {
                "status": "healthy",
                "database": db_info[1] if db_info else "unknown",
                "user": db_info[2] if db_info else "unknown", 
                "version": db_info[0].split()[0] if db_info else "unknown",
                "pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "overflow": pool.overflow(), 
                    "checked_out": pool.checkedout(),
                }
            }
            
    except Exception as e:
        logger.error("❌ Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Database initialization for development
async def create_tables():
    """Create all database tables (development only)"""
    
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot create tables in production. Use migrations instead.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("📊 Database tables created")


async def drop_tables():
    """Drop all database tables (development only)"""
    
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot drop tables in production.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("🗑️ Database tables dropped")