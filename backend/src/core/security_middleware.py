"""
Security Middleware for Convergio
Implements security headers and protections
"""

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import time
import os
from jose import jwt, JWTError, ExpiredSignatureError

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy - adjust based on your needs
        # Allow Swagger UI (FastAPI docs) assets from popular CDNs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws://localhost:* wss://localhost:*"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS - only in production
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class SecurityMiddleware:
    """Main security middleware class for authentication and validation"""
    
    def __init__(self):
        self.bearer = HTTPBearer()
        self.secret_key = os.getenv("JWT_SECRET_KEY", "convergio-default-secret-key")
    
    def validate_request(self, request: Request) -> bool:
        """Validate incoming request for security compliance"""
        try:
            # Basic validation checks
            if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
                return False
            
            # Check for suspicious headers
            suspicious_headers = ["x-forwarded-for", "x-real-ip"]
            for header in suspicious_headers:
                if header in request.headers:
                    # Additional validation could be done here
                    pass
            
            return True
        except Exception:
            return False
    
    async def validate_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
        """Validate JWT token"""
        try:
            # Use python-jose to decode; accept HS256 in dev/test, RS256 in prod when keys are configured
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=[algorithm])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Custom rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path):
            current_time = time.time()
            
            # Initialize client record if not exists
            if client_id not in self.clients:
                self.clients[client_id] = []
            
            # Remove old entries
            self.clients[client_id] = [
                timestamp for timestamp in self.clients[client_id]
                if current_time - timestamp < self.period
            ]
            
            # Check if rate limit exceeded
            if len(self.clients[client_id]) >= self.calls:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.period)}
                )
            
            # Add current request
            self.clients[client_id].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint is sensitive and needs rate limiting"""
        sensitive_paths = [
            "/api/login",
            "/api/register",
            "/api/auth",
            "/api/keys",
            "/api/agents/execute",
            "/api/costs"
        ]
        return any(path.startswith(p) for p in sensitive_paths)


# Authentication helpers
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Get the current authenticated user.
    For now, returns a mock user for development.
    In production, this should validate JWT tokens and fetch user from .database.
    """
    # Import here to avoid circular dependency
    from models.user import User
    
    # For development, return a mock admin user
    # In production, validate the JWT token and fetch user from database
    if not credentials:
        # Allow anonymous access for development
        return User(
            email="anonymous@convergio.ai",
            username="anonymous",
            full_name="Anonymous User"
        )
    
    try:
        # In production, decode JWT token
        # payload = jwt.decode(
        #     credentials.credentials,
        #     os.getenv("JWT_SECRET", "development-secret"),
        #     algorithms=["HS256"]
        # )
        # user_id = payload.get("sub")
        # Fetch user from .database...
        
        # For now, return mock admin user
        return User(
            email="admin@convergio.ai",
            username="admin",
            full_name="Admin User"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )