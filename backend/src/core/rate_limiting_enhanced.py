"""
🚦 Convergio - Enhanced Rate Limiting System
Production-ready rate limiting with Redis backend and configurable limits
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog
import redis.asyncio as redis
from fastapi import Request, HTTPException
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
    _SLOWAPI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    _rate_limit_exceeded_handler = None  # type: ignore
    RateLimitExceeded = Exception  # type: ignore
    def get_remote_address(request):  # type: ignore
        # Minimal fallback using client host header
        try:
            return request.client.host if request and request.client else "unknown"
        except Exception:
            return "unknown"
    _SLOWAPI_AVAILABLE = False

logger = structlog.get_logger(__name__)

class RateLimitResult(Enum):
    """Rate limit check result"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    WARNING = "warning"

@dataclass 
class RateLimitInfo:
    """Rate limiting information"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    limit_type: str = "general"

class EnhancedRateLimitEngine:
    """Enhanced rate limiting engine with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)
        
        # Default rate limits (per minute)
        self.default_limits = {
            "auth": {"per_minute": 5, "burst": 10},
            "api": {"per_minute": 100, "burst": 200},
            "admin": {"per_minute": 10, "burst": 20},
            "public": {"per_minute": 1000, "burst": 2000},
            "ai": {"per_minute": 50, "burst": 100}
        }
        
        # Sliding window parameters
        self.window_size = 60  # 1 minute in seconds
        self.precision = 10    # 10-second sub-windows
        
    async def configure_endpoint_limits(self, config: Dict[str, Dict[str, int]]) -> None:
        """Configure endpoint-specific rate limits"""
        self.default_limits.update(config)
        self.logger.info("Rate limiting configured", limits=self.default_limits)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Priority order: API key, user ID, IP address
        
        # Check for API key in header
        api_key = request.headers.get("Authorization")
        if api_key and api_key.startswith("Bearer "):
            return f"api_key:{api_key[7:]}"
        
        # Check for user ID (from JWT or session)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        ip_address = get_remote_address(request)
        return f"ip:{ip_address}"
    
    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path
        
        if path.startswith("/auth") or path.startswith("/login"):
            return "auth"
        elif path.startswith("/admin"):
            return "admin"  
        elif path.startswith("/api/v1/agents") or "ai" in path:
            return "ai"
        elif path.startswith("/api"):
            return "api"
        else:
            return "public"
    
    async def check_rate_limit(
        self, 
        request: Request, 
        endpoint_type: Optional[str] = None
    ) -> RateLimitInfo:
        """Check if request should be rate limited"""
        client_id = self._get_client_identifier(request)
        endpoint_type = endpoint_type or self._get_endpoint_type(request)
        
        limits = self.default_limits.get(endpoint_type, self.default_limits["public"])
        per_minute_limit = limits["per_minute"]
        limits["burst"]
        
        # Use sliding window rate limiting
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Redis key for this client/endpoint combination
        redis_key = f"rate_limit:{client_id}:{endpoint_type}"
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiry for the key
            pipe.expire(redis_key, self.window_size + 10)
            
            results = await pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            # Check if over limit
            is_allowed = current_count <= per_minute_limit
            remaining = max(0, per_minute_limit - current_count)
            reset_time = current_time + self.window_size
            
            # Calculate retry after if blocked
            retry_after = None
            if not is_allowed:
                # Find oldest request in current window
                oldest_requests = await self.redis.zrange(
                    redis_key, 0, 0, withscores=True
                )
                if oldest_requests:
                    oldest_time = oldest_requests[0][1]
                    retry_after = int(oldest_time + self.window_size - current_time)
            
            # Log rate limit events
            if not is_allowed:
                self.logger.warning(
                    "Rate limit exceeded",
                    client_id=client_id,
                    endpoint_type=endpoint_type,
                    current_count=current_count,
                    limit=per_minute_limit
                )
            elif current_count > per_minute_limit * 0.8:  # Warning at 80%
                self.logger.info(
                    "Rate limit warning",
                    client_id=client_id, 
                    endpoint_type=endpoint_type,
                    current_count=current_count,
                    limit=per_minute_limit
                )
            
            return RateLimitInfo(
                allowed=is_allowed,
                remaining=remaining,
                reset_time=reset_time,
                retry_after=retry_after,
                limit_type=endpoint_type
            )
            
        except Exception as e:
            # If Redis fails, allow the request but log the error
            self.logger.error("Rate limiting check failed", error=str(e))
            return RateLimitInfo(
                allowed=True,
                remaining=per_minute_limit,
                reset_time=current_time + self.window_size,
                limit_type=endpoint_type
            )
    
    def get_rate_limit_headers(self, rate_info: RateLimitInfo) -> Dict[str, str]:
        """Generate rate limit headers for HTTP response"""
        headers = {
            "X-RateLimit-Remaining": str(rate_info.remaining),
            "X-RateLimit-Reset": str(int(rate_info.reset_time)),
            "X-RateLimit-Type": rate_info.limit_type,
        }
        
        if rate_info.retry_after:
            headers["Retry-After"] = str(rate_info.retry_after)
            
        return headers
    
    async def cleanup_expired_entries(self) -> None:
        """Cleanup expired rate limiting entries - run periodically"""
        try:
            current_time = time.time()
            cutoff_time = current_time - self.window_size
            
            # Find all rate limit keys
            keys = await self.redis.keys("rate_limit:*")
            
            cleaned_count = 0
            for key in keys:
                # Remove expired entries from each key
                removed = await self.redis.zremrangebyscore(key, 0, cutoff_time)
                cleaned_count += removed
                
                # If key is now empty, delete it
                if await self.redis.zcard(key) == 0:
                    await self.redis.delete(key)
            
            if cleaned_count > 0:
                self.logger.info("Rate limit cleanup completed", cleaned_entries=cleaned_count)
                
        except Exception as e:
            self.logger.error("Rate limit cleanup failed", error=str(e))

class ProductionRateLimitMiddleware:
    """Production-ready rate limiting middleware"""
    
    def __init__(self, rate_engine: EnhancedRateLimitEngine, enabled: bool = True):
        self.rate_engine = rate_engine
        self.enabled = enabled
        self.logger = structlog.get_logger(__name__)
    
    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        if not self.enabled:
            return await call_next(request)
        
        # Check rate limit
        rate_info = await self.rate_engine.check_rate_limit(request)
        
        if not rate_info.allowed:
            # Rate limited - return 429
            headers = self.rate_engine.get_rate_limit_headers(rate_info)
            
            error_response = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests for {rate_info.limit_type} endpoints",
                "retry_after": rate_info.retry_after,
                "type": "rate_limit_error"
            }
            
            raise HTTPException(
                status_code=429,
                detail=error_response,
                headers=headers
            )
        
        # Process request and add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit headers to response
        rate_headers = self.rate_engine.get_rate_limit_headers(rate_info)
        for header, value in rate_headers.items():
            response.headers[header] = value
            
        return response

# Initialize rate limiter with Redis
def create_enhanced_rate_limiter(redis_client: redis.Redis, enabled: bool = True) -> Tuple[EnhancedRateLimitEngine, ProductionRateLimitMiddleware]:
    """Create enhanced rate limiting system"""
    engine = EnhancedRateLimitEngine(redis_client)
    middleware = ProductionRateLimitMiddleware(engine, enabled)
    
    return engine, middleware

def get_slowapi_limiter() -> Limiter:
    """Get slowapi limiter for backwards compatibility using configured Redis"""
    if not _SLOWAPI_AVAILABLE:
        # Return a minimal shim that won't be used, but keeps attribute presence
        class _Shim:  # pragma: no cover
            def __init__(self):
                self.enabled = False
        return _Shim()  # type: ignore
    try:
        from .config import get_settings
        s = get_settings()
        storage = s.REDIS_URL
    except Exception:
        storage = "redis://localhost:6379/1"
    return Limiter(  # type: ignore
        key_func=get_remote_address,
        storage_uri=storage,
        enabled=True,
        headers_enabled=True,
        default="1000/minute"  # Conservative default
    )