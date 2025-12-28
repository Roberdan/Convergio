"""
Rate Limiting System for API Protection
- In-memory TokenBucket and SlidingWindowRateLimiter for unit/perf tests
- Async Redis-backed middleware for production FastAPI usage
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis
try:
    # Prefer core config
    from .config import get_settings  # type: ignore
except Exception:
    # Fallback to legacy location if needed
    from agents.utils.config import get_settings  # type: ignore


# -----------------------
# In-memory implementations
# -----------------------

@dataclass
class TokenBucket:
    capacity: int
    refill_rate: int  # tokens per second
    tokens: float = 0
    last_refill_timestamp: float = 0.0

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last_refill_timestamp = time.time()

    def refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill_timestamp
        added = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + added)
        self.last_refill_timestamp = now

    def consume(self, amount: int = 1) -> bool:
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class SlidingWindowRateLimiter:
    """Simple sliding window limiter per identifier (in-memory)."""

    def __init__(self, requests_per_minute: int = 60, window_size: int = 60) -> None:
        self.rpm = requests_per_minute
        self.window = window_size
        self._store: Dict[str, list[float]] = {}

    def allow_request(self, identifier: str) -> bool:
        now = time.time()
        window_start = now - self.window
        q = self._store.setdefault(identifier, [])
        # Drop old
        while q and q[0] < window_start:
            q.pop(0)
        if len(q) < self.rpm:
            q.append(now)
            return True
        return False


class RateLimiter:
    """In-memory rate limiter using TokenBucket, API shaped for tests."""

    def __init__(self, requests_per_second: int = 10, burst_size: int = 20, redis_client: Any | None = None) -> None:
        self.rps = requests_per_second
        self.burst = burst_size
        self._buckets: Dict[str, TokenBucket] = {}
        self._redis = redis_client  # optional for distributed tests

    def _get_bucket(self, key: str) -> TokenBucket:
        bucket = self._buckets.get(key)
        if not bucket:
            bucket = TokenBucket(capacity=self.burst, refill_rate=self.rps)
            self._buckets[key] = bucket
        return bucket

    def allow_request(self, identifier: str) -> bool:
        # If a Redis client is supplied, simulate a distributed counter
        if self._redis is not None:
            try:
                count = self._redis.incr(f"rate:{identifier}")
                ttl = self._redis.ttl(f"rate:{identifier}")
                if ttl < 0:
                    self._redis.expire(f"rate:{identifier}", 60)
                return count <= self.burst
            except Exception:
                # Fallback to local bucket on Redis error
                return self._get_bucket(identifier).consume(1)
        return self._get_bucket(identifier).consume(1)
    
    def is_allowed(self, identifier: str) -> bool:
        """Alias for allow_request for backward compatibility"""
        return self.allow_request(identifier)

    async def allow_request_async(self, identifier: str) -> bool:
        return self.allow_request(identifier)

    def get_rate_limit_headers(self, identifier: str) -> Dict[str, str]:
        bucket = self._get_bucket(identifier)
        return {
            "X-RateLimit-Limit": str(self.burst),
            "X-RateLimit-Remaining": str(max(0, int(bucket.tokens))),
            "X-RateLimit-Reset": str(int(bucket.last_refill_timestamp + 1)),
        }

    def get_rate_limit_response(self, identifier: str) -> Dict[str, Any]:
        return {
            "status_code": 429,
            "headers": {"Retry-After": "1"},
            "body": {"error": "Rate limit exceeded", "retry_after": 1},
        }

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    burst_size: int = 10
    window_size: int = 60  # seconds
    block_duration: int = 300  # seconds to block after violation

class RedisBackedRateLimiter:
    """Token bucket rate limiter with Redis backend (async, for middleware)."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.settings = get_settings()

    async def _get_bucket_key(self, identifier: str) -> str:
        return f"rate_limit:{identifier}"

    async def _get_block_key(self, identifier: str) -> str:
        return f"rate_limit_blocked:{identifier}"

    async def is_blocked(self, identifier: str) -> bool:
        block_key = await self._get_block_key(identifier)
        return await self.redis.exists(block_key)

    async def check_rate_limit(self, identifier: str) -> Dict[str, Any]:
        if await self.is_blocked(identifier):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

        bucket_key = await self._get_bucket_key(identifier)
        now = int(time.time())

        bucket_data = await self.redis.hgetall(bucket_key)

        if not bucket_data:
            tokens = self.settings.rate_limit_burst_size
            last_refill = now
        else:
            tokens = int(bucket_data.get(b"tokens", 0))
            last_refill = int(bucket_data.get(b"last_refill", now))

        time_passed = now - last_refill
        tokens_to_add = (time_passed // self.settings.rate_limit_window_size) * self.settings.rate_limit_requests_per_minute

        tokens = min(self.settings.rate_limit_burst_size, tokens + tokens_to_add)

        if tokens_to_add > 0:
            last_refill = now - (time_passed % self.settings.rate_limit_window_size)

        if tokens > 0:
            tokens -= 1
            allowed = True
        else:
            allowed = False

        await self.redis.hset(bucket_key, mapping={"tokens": tokens, "last_refill": last_refill})
        await self.redis.expire(bucket_key, self.settings.rate_limit_window_size * 2)

        if not allowed:
            await self._block_identifier(identifier)

        return {"allowed": allowed, "remaining_tokens": max(0, tokens), "reset_time": last_refill + self.settings.rate_limit_window_size}

    async def _block_identifier(self, identifier: str):
        block_key = await self._get_block_key(identifier)
        await self.redis.setex(block_key, self.settings.rate_limit_block_duration, "blocked")

    async def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        bucket_key = await self._get_bucket_key(identifier)
        bucket_data = await self.redis.hgetall(bucket_key)

        if not bucket_data:
            return {
                "tokens": self.settings.rate_limit_burst_size,
                "max_tokens": self.settings.rate_limit_burst_size,
                "reset_time": int(time.time()) + self.settings.rate_limit_window_size,
            }

        tokens = int(bucket_data.get(b"tokens", 0))
        last_refill = int(bucket_data.get(b"last_refill", int(time.time())))
        return {"tokens": tokens, "max_tokens": self.settings.rate_limit_burst_size, "reset_time": last_refill + self.settings.rate_limit_window_size}

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)
        
        # Get identifier (IP address or user ID)
        identifier = self._get_identifier(request)
        
        try:
            # Check rate limit
            # rate_limiter can be RedisBackedRateLimiter
            result = await self.rate_limiter.check_rate_limit(identifier)
            
            if not result['allowed']:
                return JSONResponse(
                    status_code=429,
                    content={
                        'error': 'Rate limit exceeded',
                        'retry_after': result['reset_time'] - int(time.time()),
                        'detail': 'Too many requests. Please try again later.'
                    }
                )
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers['X-RateLimit-Limit'] = str(self.rate_limiter.settings.rate_limit_requests_per_minute)
            response.headers['X-RateLimit-Remaining'] = str(result['remaining_tokens'])
            response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log error and continue without rate limiting
            print(f"Rate limiting error: {e}")
            return await call_next(request)
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = [
            '/health',
            '/metrics',
            '/docs',
            '/openapi.json'
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP address)"""
        # Get real IP address (considering proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'

# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

async def get_rate_limiter() -> Optional[RedisBackedRateLimiter]:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        try:
            # Initialize Redis client
            redis_client = redis.Redis(
                host=get_settings().redis_host,
                port=get_settings().redis_port,
                db=get_settings().redis_db,
                decode_responses=False
            )
            # Test connection
            await redis_client.ping()
            _rate_limiter = RedisBackedRateLimiter(redis_client)
        except Exception as e:
            print(f"⚠️ Warning: Could not connect to Redis for rate limiting: {e}")
            print("Rate limiting will be disabled for this session")
            return None
    return _rate_limiter

async def create_rate_limit_middleware() -> Optional[RateLimitMiddleware]:
    """Create rate limit middleware instance"""
    rate_limiter = await get_rate_limiter()
    if not rate_limiter:
        return None
    return RateLimitMiddleware(rate_limiter)
