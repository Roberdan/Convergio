"""
🚨 Convergio - Enhanced Error Handling System
Fail-fast error handling with proper categorization, retry logic, and circuit breakers
"""

import asyncio
import time
import traceback
import uuid
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger(__name__)

class ErrorCategory(Enum):
    """Error categorization for different handling strategies"""
    FATAL = "fatal"                    # Terminate process immediately
    RECOVERABLE = "recoverable"        # Retry with backoff
    WARNING = "warning"                # Log and continue
    VALIDATION = "validation"          # Input validation errors
    SECURITY = "security"              # Security-related errors

class ServiceStatus(Enum):
    """Service status for circuit breaker"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    FAILED = "failed"
    CIRCUIT_OPEN = "circuit_open"

@dataclass
class ErrorContext:
    """Enhanced error context with correlation tracking"""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service: str = "unknown"
    operation: str = "unknown"
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
class StartupError(Exception):
    """Critical startup error - should terminate process"""
    pass

class ServiceUnavailableError(Exception):
    """Service temporarily unavailable - recoverable"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

class SecurityError(Exception):
    """Security-related error"""
    pass

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3

class CircuitBreaker:
    """Circuit breaker for external services"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.failure_count = 0
        self.last_failure_time = 0
        self.status = ServiceStatus.HEALTHY
        self.half_open_calls = 0
        
    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker"""
        now = time.time()
        
        if self.status == ServiceStatus.HEALTHY:
            return True
        elif self.status == ServiceStatus.CIRCUIT_OPEN:
            if now - self.last_failure_time > self.config.recovery_timeout:
                self.status = ServiceStatus.DEGRADED
                self.half_open_calls = 0
                logger.info(f"Circuit breaker {self.name} entering half-open state")
                return True
            return False
        elif self.status == ServiceStatus.DEGRADED:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def on_success(self):
        """Record successful operation"""
        if self.status == ServiceStatus.DEGRADED:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.status = ServiceStatus.HEALTHY
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} returning to healthy state")
        else:
            self.failure_count = max(0, self.failure_count - 1)
    
    def on_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            if self.status != ServiceStatus.CIRCUIT_OPEN:
                self.status = ServiceStatus.CIRCUIT_OPEN
                logger.error(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
        elif self.status == ServiceStatus.DEGRADED:
            self.status = ServiceStatus.CIRCUIT_OPEN
            logger.error(f"Circuit breaker {self.name} opened during half-open state")

class EnhancedErrorHandler:
    """Enhanced error handling system"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[str, int] = {}
        
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error for appropriate handling"""
        if isinstance(error, (StartupError, SystemExit, KeyboardInterrupt)):
            return ErrorCategory.FATAL
        elif isinstance(error, (ConnectionError, TimeoutError, ServiceUnavailableError)):
            return ErrorCategory.RECOVERABLE
        elif isinstance(error, ValidationError):
            return ErrorCategory.VALIDATION
        elif isinstance(error, SecurityError):
            return ErrorCategory.SECURITY
        elif isinstance(error, (ImportError, ModuleNotFoundError)) and "startup" in str(error).lower():
            return ErrorCategory.FATAL
        else:
            # Default to recoverable for unknown errors
            return ErrorCategory.RECOVERABLE
    
    def handle_startup_error(self, error: Exception, context: ErrorContext) -> None:
        """Handle startup error with fail-fast behavior"""
        self.logger.error(
            "❌ FATAL STARTUP ERROR - Terminating process",
            error_id=context.error_id,
            service=context.service,
            operation=context.operation,
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            metadata=context.metadata
        )
        
        # In production, exit immediately
        # In development/test, raise for debugging
        import os
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            import sys
            sys.exit(1)
        else:
            raise StartupError(f"Startup failed in {context.service}: {error}") from error
    
    def log_error_context(self, error: Exception, context: ErrorContext) -> None:
        """Log error with structured context"""
        error_category = self.categorize_error(error)
        
        log_data = {
            "error_id": context.error_id,
            "error_category": error_category.value,
            "service": context.service,
            "operation": context.operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": context.timestamp,
            "metadata": context.metadata
        }
        
        if context.user_id:
            log_data["user_id"] = context.user_id
        if context.request_id:
            log_data["request_id"] = context.request_id
        
        if error_category == ErrorCategory.FATAL:
            log_data["traceback"] = traceback.format_exc()
            self.logger.error("❌ FATAL ERROR", **log_data)
        elif error_category == ErrorCategory.SECURITY:
            # Don't log sensitive details for security errors
            log_data.pop("traceback", None)
            self.logger.error("🔒 SECURITY ERROR", **log_data)
        elif error_category == ErrorCategory.RECOVERABLE:
            self.logger.warning("⚠️ RECOVERABLE ERROR", **log_data)
        else:
            self.logger.info("ℹ️ ERROR INFO", **log_data)
    
    async def retry_with_backoff(
        self, 
        operation: Callable,
        context: ErrorContext,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ) -> Any:
        """Retry operation with exponential backoff"""
        if retry_config is None:
            retry_config = RetryConfig()
            
        last_error = None
        delay = retry_config.initial_delay
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                # Check circuit breaker
                if circuit_breaker and not circuit_breaker.should_allow_request():
                    raise ServiceUnavailableError(f"Circuit breaker {circuit_breaker.name} is open")
                
                # Attempt operation
                result = await operation() if asyncio.iscoroutinefunction(operation) else operation()
                
                # Success - update circuit breaker and return
                if circuit_breaker:
                    circuit_breaker.on_success()
                
                if attempt > 0:
                    self.logger.info(
                        "✅ Operation succeeded after retry",
                        error_id=context.error_id,
                        service=context.service,
                        operation=context.operation,
                        attempt=attempt + 1
                    )
                
                return result
                
            except Exception as error:
                last_error = error
                
                # Update circuit breaker on failure
                if circuit_breaker:
                    circuit_breaker.on_failure()
                
                # Don't retry fatal errors
                if self.categorize_error(error) == ErrorCategory.FATAL:
                    raise
                
                # Last attempt - don't wait
                if attempt == retry_config.max_retries:
                    break
                
                # Log retry attempt
                self.logger.warning(
                    "🔄 Retrying operation",
                    error_id=context.error_id,
                    service=context.service,
                    operation=context.operation,
                    attempt=attempt + 1,
                    max_retries=retry_config.max_retries,
                    delay=delay,
                    error_type=type(error).__name__,
                    error_message=str(error)
                )
                
                # Wait before retry with jitter
                if retry_config.jitter:
                    import random
                    actual_delay = delay * (0.5 + 0.5 * random.random())
                else:
                    actual_delay = delay
                    
                await asyncio.sleep(actual_delay)
                
                # Increase delay for next attempt
                delay = min(
                    delay * retry_config.exponential_base,
                    retry_config.max_delay
                )
        
        # All retries failed
        self.log_error_context(last_error, context)
        raise last_error
    
    def get_circuit_breaker(self, service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        
        return self.circuit_breakers[service_name]
    
    @asynccontextmanager
    async def error_context(self, service: str, operation: str, **metadata):
        """Context manager for error handling"""
        context = ErrorContext(
            service=service,
            operation=operation,
            metadata=metadata
        )
        
        try:
            yield context
        except Exception as error:
            self.log_error_context(error, context)
            
            # Handle based on category
            category = self.categorize_error(error)
            if category == ErrorCategory.FATAL:
                self.handle_startup_error(error, context)
            else:
                raise

# Global error handler instance
error_handler = EnhancedErrorHandler()

def handle_startup_validation(required_services: List[str]) -> None:
    """Validate required services are available at startup.

    In test environment, skip strict validation to allow the app to boot
    with in-memory/sqlite fallback and mocked services.
    """
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "test":
        logger.warning("🧪 Skipping strict startup validation in test environment")
        return

    logger.info("🔍 Validating required services", services=required_services)
    
    errors = []
    
    for service in required_services:
        try:
            if service == "database":
                # Check database connection
                if not all([
                    os.getenv("POSTGRES_HOST"),
                    os.getenv("POSTGRES_DB"),
                    os.getenv("POSTGRES_USER"),
                    os.getenv("POSTGRES_PASSWORD")
                ]):
                    errors.append("Database configuration incomplete")
            
            elif service == "redis":
                # Accept either REDIS_HOST or consolidated REDIS_URL
                if not (os.getenv("REDIS_HOST") or os.getenv("REDIS_URL")):
                    errors.append("Redis configuration incomplete")
            
            elif service == "ai_apis":
                if not any([
                    os.getenv("OPENAI_API_KEY"),
                    os.getenv("ANTHROPIC_API_KEY")
                ]):
                    errors.append("No AI API keys configured")
                    
        except Exception as e:
            errors.append(f"{service}: {str(e)}")
    
    if errors:
        error_msg = f"Service validation failed: {'; '.join(errors)}"
        context = ErrorContext(service="startup", operation="validation")
        error_handler.handle_startup_error(StartupError(error_msg), context)
    
    logger.info("✅ Service validation completed successfully")

async def validate_service_connectivity() -> Dict[str, bool]:
    """Validate actual connectivity to required services"""
    results = {}
    
    # Database connectivity
    try:
        from .database import get_db_session
        from sqlalchemy import text as _sql_text
        async with get_db_session() as session:
            await session.execute(_sql_text("SELECT 1"))
        results["database"] = True
        logger.info("✅ Database connectivity verified")
    except Exception as e:
        results["database"] = False
        logger.error("❌ Database connectivity failed", error=str(e))
    
    # Redis connectivity
    try:
        from .redis import get_redis_client
        redis_client = get_redis_client()
        await redis_client.ping()
        results["redis"] = True
        logger.info("✅ Redis connectivity verified")
    except Exception as e:
        results["redis"] = False
        logger.error("❌ Redis connectivity failed", error=str(e))
    
    return results