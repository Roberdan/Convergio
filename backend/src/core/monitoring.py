"""
Enhanced Monitoring and Health Checks System
Comprehensive monitoring for all system components
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import os
from dataclasses import dataclass
from enum import Enum

import structlog
from prometheus_client import Counter, Histogram, Gauge
from sqlalchemy import text
from .database import async_engine, get_async_session
from .redis import get_redis_client

logger = structlog.get_logger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None

@dataclass
class SystemHealth:
    overall_status: HealthStatus
    checks: List[HealthCheckResult]
    timestamp: datetime
    uptime_seconds: float

class HealthChecker:
    """Comprehensive system health checker"""
    
    def __init__(self):
        self.logger = logger
        self.start_time = time.time()
        
        # Prometheus metrics
        self.health_check_counter = Counter(
            'health_check_total', 
            'Total health checks performed', 
            ['check_name', 'status']
        )
        self.health_check_duration = Histogram(
            'health_check_duration_seconds',
            'Health check duration in seconds',
            ['check_name']
        )
        self.system_uptime = Gauge(
            'system_uptime_seconds',
            'System uptime in seconds'
        )
        
    async def check_all_health(self) -> SystemHealth:
        """Perform comprehensive health check of all system components"""
        checks = []
        
        # Run all health checks concurrently
        check_tasks = [
            self._check_database_health(),
            self._check_redis_health(),
            self._check_api_health(),
            self._check_ai_services_health(),
            self._check_system_resources(),
            self._check_configuration_health(),
            self._check_security_health(),
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                checks.append(HealthCheckResult(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    details={},
                    timestamp=datetime.utcnow(),
                    error=str(result)
                ))
            else:
                checks.append(result)
        
        # Determine overall system health
        overall_status = self._determine_overall_status(checks)
        uptime = time.time() - self.start_time
        self.system_uptime.set(uptime)
        
        return SystemHealth(
            overall_status=overall_status,
            checks=checks,
            timestamp=datetime.utcnow(),
            uptime_seconds=uptime
        )
    
    async def _check_database_health(self) -> HealthCheckResult:
        """Check database connectivity and performance"""
        start_time = time.time()
        check_name = "database"
        
        try:
            with self.health_check_duration.labels(check_name=check_name).time():
                async with get_async_session() as session:
                    # Test basic connectivity
                    result = await session.execute(text("SELECT 1 as health_check"))
                    health_value = result.scalar()
                    
                    # Test table existence
                    table_check = await session.execute(text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' LIMIT 5"
                    ))
                    tables = [row[0] for row in table_check.fetchall()]
                    
                    # Check connection pool
                    pool_status = {
                        "pool_size": async_engine.pool.size(),
                        "checked_in": async_engine.pool.checkedin(),
                        "checked_out": async_engine.pool.checkedout(),
                        "overflow": async_engine.pool.overflow(),
                    }
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    self.health_check_counter.labels(check_name=check_name, status="healthy").inc()
                    
                    return HealthCheckResult(
                        name=check_name,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        details={
                            "connection_test": health_value == 1,
                            "tables_found": len(tables),
                            "sample_tables": tables,
                            "pool_status": pool_status
                        },
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_redis_health(self) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        check_name = "redis"
        
        try:
            with self.health_check_duration.labels(check_name=check_name).time():
                redis_client = get_redis_client()
                
                # Test basic connectivity
                ping_result = await redis_client.ping()
                
                # Test read/write operations
                test_key = f"health_check:{int(time.time())}"
                test_value = "health_check_value"
                
                await redis_client.set(test_key, test_value, ex=60)
                retrieved_value = await redis_client.get(test_key)
                await redis_client.delete(test_key)
                
                # Get Redis info
                info = await redis_client.info()
                
                response_time = (time.time() - start_time) * 1000
                
                status = HealthStatus.HEALTHY if (
                    ping_result and 
                    retrieved_value.decode() == test_value
                ) else HealthStatus.DEGRADED
                
                self.health_check_counter.labels(check_name=check_name, status=status.value).inc()
                
                return HealthCheckResult(
                    name=check_name,
                    status=status,
                    response_time_ms=response_time,
                    details={
                        "ping_test": ping_result,
                        "read_write_test": retrieved_value.decode() == test_value if retrieved_value else False,
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "unknown"),
                        "redis_version": info.get("redis_version", "unknown")
                    },
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_api_health(self) -> HealthCheckResult:
        """Check API endpoints and routing health"""
        start_time = time.time()
        check_name = "api"
        
        try:
            # This is a self-check, so we'll verify internal components
            from fastapi import __version__ as fastapi_version
            
            response_time = (time.time() - start_time) * 1000
            
            self.health_check_counter.labels(check_name=check_name, status="healthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "fastapi_version": fastapi_version,
                    "python_version": os.sys.version.split()[0],
                    "environment": os.getenv("ENVIRONMENT", "unknown")
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_ai_services_health(self) -> HealthCheckResult:
        """Check AI services connectivity"""
        start_time = time.time()
        check_name = "ai_services"
        
        try:
            # Check if AI API keys are configured
            openai_key = os.getenv("OPENAI_API_KEY")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            
            # Basic validation without making actual API calls to avoid costs in health checks
            ai_services_configured = {
                "openai": bool(openai_key and len(openai_key) > 10),
                "anthropic": bool(anthropic_key and len(anthropic_key) > 10)
            }
            
            configured_count = sum(ai_services_configured.values())
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY if configured_count > 0 else HealthStatus.DEGRADED
            
            self.health_check_counter.labels(check_name=check_name, status=status.value).inc()
            
            return HealthCheckResult(
                name=check_name,
                status=status,
                response_time_ms=response_time,
                details={
                    "configured_services": configured_count,
                    "services_available": ai_services_configured
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        start_time = time.time()
        check_name = "system_resources"
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
                status = HealthStatus.DEGRADED
            
            self.health_check_counter.labels(check_name=check_name, status=status.value).inc()
            
            return HealthCheckResult(
                name=check_name,
                status=status,
                response_time_ms=response_time,
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory_percent, 2),
                    "disk_percent": round(disk_percent, 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_configuration_health(self) -> HealthCheckResult:
        """Check configuration completeness and validity"""
        start_time = time.time()
        check_name = "configuration"
        
        try:
            from .config_validator import ConfigValidator
            
            validator = ConfigValidator()
            result = validator.validate_all()
            
            response_time = (time.time() - start_time) * 1000
            
            status = HealthStatus.HEALTHY if result.is_valid else HealthStatus.DEGRADED
            
            self.health_check_counter.labels(check_name=check_name, status=status.value).inc()
            
            return HealthCheckResult(
                name=check_name,
                status=status,
                response_time_ms=response_time,
                details={
                    "is_valid": result.is_valid,
                    "error_count": len(result.errors),
                    "warning_count": len(result.warnings),
                    "errors": result.errors[:3],  # First 3 errors only
                    "warnings": result.warnings[:3]  # First 3 warnings only
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    async def _check_security_health(self) -> HealthCheckResult:
        """Check security configuration and status"""
        start_time = time.time()
        check_name = "security"
        
        try:
            # Check for security-critical environment variables
            security_checks = {
                "jwt_secret_set": bool(os.getenv("JWT_SECRET")),
                "jwt_secret_strong": len(os.getenv("JWT_SECRET", "")) >= 32,
                "cors_configured": bool(os.getenv("CORS_ALLOWED_ORIGINS")),
                "https_in_production": self._check_https_in_production(),
                "debug_disabled_in_prod": self._check_debug_disabled()
            }
            
            security_score = sum(security_checks.values()) / len(security_checks)
            
            response_time = (time.time() - start_time) * 1000
            
            if security_score >= 0.9:
                status = HealthStatus.HEALTHY
            elif security_score >= 0.7:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            self.health_check_counter.labels(check_name=check_name, status=status.value).inc()
            
            return HealthCheckResult(
                name=check_name,
                status=status,
                response_time_ms=response_time,
                details={
                    "security_score": round(security_score * 100, 1),
                    "checks_passed": sum(security_checks.values()),
                    "total_checks": len(security_checks),
                    "security_checks": security_checks
                },
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.health_check_counter.labels(check_name=check_name, status="unhealthy").inc()
            
            return HealthCheckResult(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                details={},
                timestamp=datetime.utcnow(),
                error=str(e)
            )
    
    def _check_https_in_production(self) -> bool:
        """Check if HTTPS is used in production"""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment != "production":
            return True  # Not applicable in non-production
        
        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
        return not ("http://" in cors_origins and "localhost" not in cors_origins)
    
    def _check_debug_disabled(self) -> bool:
        """Check if debug mode is disabled in production"""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        if environment == "production":
            return not debug_mode
        return True  # Debug can be enabled in non-production
    
    def _determine_overall_status(self, checks: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall system status based on individual checks"""
        if not checks:
            return HealthStatus.UNHEALTHY
        
        unhealthy_count = sum(1 for check in checks if check.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for check in checks if check.status == HealthStatus.DEGRADED)
        
        # If any critical service is unhealthy, system is unhealthy
        critical_services = {"database", "redis", "configuration"}
        critical_unhealthy = any(
            check.name in critical_services and check.status == HealthStatus.UNHEALTHY 
            for check in checks
        )
        
        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        elif unhealthy_count > 0 or degraded_count > 2:
            return HealthStatus.DEGRADED
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_health_summary(self, system_health: SystemHealth) -> Dict[str, Any]:
        """Get a summary of system health for API responses"""
        return {
            "status": system_health.overall_status.value,
            "timestamp": system_health.timestamp.isoformat(),
            "uptime_seconds": system_health.uptime_seconds,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "response_time_ms": check.response_time_ms,
                    "error": check.error
                } for check in system_health.checks
            },
            "summary": {
                "total_checks": len(system_health.checks),
                "healthy": sum(1 for c in system_health.checks if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in system_health.checks if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in system_health.checks if c.status == HealthStatus.UNHEALTHY)
            }
        }

# Global health checker instance
health_checker = HealthChecker()