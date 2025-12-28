"""
🚀 Convergio - Redis Cache Management
High-performance async Redis with connection pooling
"""

import json
from typing import Any, Optional
import structlog
import redis.asyncio as redis

from .config import get_settings

logger = structlog.get_logger()

# Global Redis client
redis_client: Optional[redis.Redis] = None


class _NoOpRedis:
    async def ping(self):
        return True
    async def set(self, *args, **kwargs):
        return True
    async def setex(self, *args, **kwargs):
        return True
    async def get(self, *args, **kwargs):
        return None
    async def delete(self, *args, **kwargs):
        return True
    async def info(self):
        return {}
    async def aclose(self):
        return None


async def init_redis() -> None:
    """Initialize Redis connection pool"""
    
    global redis_client
    
    settings = get_settings()
    
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_POOL_SIZE,
            retry_on_timeout=True,
            decode_responses=True,
        )
        
        # Test connection
        await redis_client.ping()
        
        # Hide credentials from URL for logging
        safe_url = settings.REDIS_URL
        if "@" in safe_url:
            safe_url = safe_url.split("@")[1]
        logger.info("✅ Redis initialized successfully", url=safe_url)
        
    except Exception as e:
        logger.error("❌ Failed to initialize Redis", error=str(e))
        raise


async def close_redis() -> None:
    """Close Redis connections"""
    
    global redis_client
    
    if redis_client:
        try:
            await redis_client.aclose()
            logger.info("✅ Redis connections closed")
        except Exception as e:
            logger.error("❌ Error closing Redis", error=str(e))
        finally:
            redis_client = None


def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    
    if redis_client is None:
        # Provide a no-op client during tests to avoid failures when Redis isn't available
        import os
        if os.getenv("ENVIRONMENT", "development").lower() == "test":
            return _NoOpRedis()
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    
    return redis_client


# Cache operations
async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set cache value with TTL"""
    
    client = get_redis_client()
    
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await client.setex(key, ttl, value)
    except Exception as e:
        logger.error("❌ Cache set failed", key=key, error=str(e))
        return False


async def cache_get(key: str) -> Optional[Any]:
    """Get cache value"""
    
    client = get_redis_client()
    
    try:
        value = await client.get(key)
        if value:
            try:
                return json.loads(value)
            except Exception:
                return value
        return None
    except Exception as e:
        logger.error("❌ Cache get failed", key=key, error=str(e))
        return None


async def cache_delete(key: str) -> bool:
    """Delete cache key"""
    
    client = get_redis_client()
    
    try:
        return bool(await client.delete(key))
    except Exception as e:
        logger.error("❌ Cache delete failed", key=key, error=str(e))
        return False