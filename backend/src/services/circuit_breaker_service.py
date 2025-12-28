"""
🚦 Circuit Breaker Service for Cost Limits
Automatic protection against budget overruns with intelligent suspension
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from enum import Enum

import structlog

from ..core.database import get_async_session
from ..services.budget_monitor_service import budget_monitor

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class SuspensionReason(str, Enum):
    """Reasons for API suspension"""
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"
    MONTHLY_LIMIT_EXCEEDED = "monthly_limit_exceeded"
    PROVIDER_CREDITS_EXHAUSTED = "provider_credits_exhausted"
    COST_SPIKE_DETECTED = "cost_spike_detected"
    MANUAL_OVERRIDE = "manual_override"


class CircuitBreakerService:
    """Intelligent circuit breaker for cost limit protection"""
    
    def __init__(self):
        """Initialize circuit breaker service"""
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.recovery_timeout = 300  # 5 minutes
        self.failure_threshold = 3  # Open after 3 violations
        
        # Suspension tracking
        self.suspended_providers = set()
        self.suspended_agents = set()
        self.suspension_reasons = {}
        self.override_codes = {}  # Emergency override codes
        
        # Monitoring settings
        self.check_interval = 60  # Check every minute
        self.grace_period = 180  # 3 minutes grace for small overruns
        
        logger.info("🚦 Circuit breaker service initialized")
    
    async def check_should_block_request(
        self,
        provider: str,
        agent_id: Optional[str] = None,
        estimated_cost: Optional[float] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a request should be blocked due to cost limits
        
        Returns: (should_block, block_reason)
        """
        
        try:
            # Quick check - if circuit is open, block immediately
            if self.circuit_state == CircuitState.OPEN:
                return True, {
                    "reason": "circuit_open",
                    "message": "Circuit breaker is open - API calls suspended",
                    "state": self.circuit_state.value,
                    "suspension_reasons": list(self.suspension_reasons.keys())
                }
            
            # Check if specific provider is suspended
            if provider in self.suspended_providers:
                return True, {
                    "reason": "provider_suspended",
                    "message": f"Provider {provider} is suspended due to credit limits",
                    "provider": provider,
                    "suspension_reason": self.suspension_reasons.get(provider)
                }
            
            # Check if specific agent is suspended
            if agent_id and agent_id in self.suspended_agents:
                return True, {
                    "reason": "agent_suspended", 
                    "message": f"Agent {agent_id} is suspended due to budget limits",
                    "agent_id": agent_id,
                    "suspension_reason": self.suspension_reasons.get(agent_id)
                }
            
            # Get current budget status
            budget_status = await budget_monitor.get_budget_status_summary()
            
            # Check if circuit breaker should trigger
            if budget_status["circuit_breaker_active"]:
                await self._open_circuit("Budget limits exceeded")
                return True, {
                    "reason": "budget_limits_exceeded",
                    "message": "Budget limits exceeded - circuit breaker activated",
                    "budget_status": budget_status
                }
            
            # Proactive check for potential overspend
            if estimated_cost and estimated_cost > 0:
                daily_util = budget_status["daily_utilization"]
                monthly_util = budget_status["monthly_utilization"]
                
                # Block if adding this cost would exceed 100%
                if daily_util >= 95 or monthly_util >= 95:
                    return True, {
                        "reason": "would_exceed_limits",
                        "message": f"Request would exceed budget limits (daily: {daily_util:.1f}%, monthly: {monthly_util:.1f}%)",
                        "estimated_cost": estimated_cost,
                        "current_utilization": {
                            "daily": daily_util,
                            "monthly": monthly_util
                        }
                    }
            
            # Half-open state - allow limited requests
            if self.circuit_state == CircuitState.HALF_OPEN:
                # Allow request but monitor closely
                logger.info("🚦 Allowing request in half-open state", provider=provider, agent_id=agent_id)
                return False, None
            
            # Normal operation - allow request
            return False, None
            
        except Exception as e:
            logger.error("❌ Failed to check circuit breaker", error=str(e))
            # Fail safe - allow request if check fails
            return False, None
    
    async def record_api_call_result(
        self,
        provider: str,
        agent_id: Optional[str],
        cost: float,
        success: bool = True
    ):
        """Record the result of an API call for monitoring"""
        
        try:
            if success:
                # Successful call - check if we should transition states
                if self.circuit_state == CircuitState.HALF_OPEN:
                    await self._close_circuit("Successful API call in half-open state")
            else:
                # Failed call - increment failure count
                self.failure_count += 1
                self.last_failure_time = datetime.utcnow()
                
                if self.failure_count >= self.failure_threshold:
                    await self._open_circuit(f"Too many failures: {self.failure_count}")
            
            # Check for cost anomalies
            if cost > 1.0:  # High cost call
                await self._record_cost_spike(provider, agent_id, cost)
            
        except Exception as e:
            logger.error("❌ Failed to record API call result", error=str(e))
    
    async def _open_circuit(self, reason: str):
        """Open the circuit breaker"""
        
        if self.circuit_state != CircuitState.OPEN:
            self.circuit_state = CircuitState.OPEN
            self.last_failure_time = datetime.utcnow()
            
            logger.critical("🚨 Circuit breaker OPENED", reason=reason)
            
            # Create alert
            await self._create_circuit_alert("circuit_opened", "critical", reason)
    
    async def _close_circuit(self, reason: str):
        """Close the circuit breaker"""
        
        if self.circuit_state != CircuitState.CLOSED:
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            
            logger.info("✅ Circuit breaker CLOSED", reason=reason)
            
            # Create alert
            await self._create_circuit_alert("circuit_closed", "info", reason)
    
    async def _half_open_circuit(self, reason: str):
        """Set circuit to half-open state"""
        
        if self.circuit_state == CircuitState.OPEN:
            self.circuit_state = CircuitState.HALF_OPEN
            
            logger.info("🔄 Circuit breaker HALF-OPEN", reason=reason)
            
            # Create alert
            await self._create_circuit_alert("circuit_half_open", "warning", reason)
    
    async def _record_cost_spike(self, provider: str, agent_id: Optional[str], cost: float):
        """Record a cost spike for monitoring"""
        
        f"spike_{provider}_{agent_id}_{datetime.utcnow().isoformat()}"
        
        logger.warning("💸 Cost spike detected",
                      provider=provider,
                      agent_id=agent_id,
                      cost=cost)
        
        # Store spike data for analysis
        spike_data = {
            "provider": provider,
            "agent_id": agent_id,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if cost > 5.0 else "medium"
        }
        
        # Would store in Redis/database in production
        logger.info("📊 Cost spike recorded", spike_data=spike_data)
    
    async def suspend_provider(
        self,
        provider: str,
        reason: SuspensionReason,
        duration_minutes: Optional[int] = None
    ):
        """Suspend a specific provider"""
        
        self.suspended_providers.add(provider)
        self.suspension_reasons[provider] = {
            "reason": reason.value,
            "suspended_at": datetime.utcnow().isoformat(),
            "duration_minutes": duration_minutes,
            "auto_resume": duration_minutes is not None
        }
        
        logger.critical("🚫 Provider suspended",
                       provider=provider,
                       reason=reason.value,
                       duration_minutes=duration_minutes)
        
        # Auto-resume if duration specified
        if duration_minutes:
            asyncio.create_task(self._auto_resume_provider(provider, duration_minutes))
        
        await self._create_circuit_alert(
            "provider_suspended",
            "critical",
            f"Provider {provider} suspended: {reason.value}"
        )
    
    async def suspend_agent(
        self,
        agent_id: str,
        reason: SuspensionReason,
        duration_minutes: Optional[int] = None
    ):
        """Suspend a specific agent"""
        
        self.suspended_agents.add(agent_id)
        self.suspension_reasons[agent_id] = {
            "reason": reason.value,
            "suspended_at": datetime.utcnow().isoformat(),
            "duration_minutes": duration_minutes,
            "auto_resume": duration_minutes is not None
        }
        
        logger.critical("🚫 Agent suspended",
                       agent_id=agent_id,
                       reason=reason.value,
                       duration_minutes=duration_minutes)
        
        # Auto-resume if duration specified
        if duration_minutes:
            asyncio.create_task(self._auto_resume_agent(agent_id, duration_minutes))
        
        await self._create_circuit_alert(
            "agent_suspended",
            "critical",
            f"Agent {agent_id} suspended: {reason.value}"
        )
    
    async def _auto_resume_provider(self, provider: str, duration_minutes: int):
        """Automatically resume a provider after duration"""
        
        await asyncio.sleep(duration_minutes * 60)
        
        if provider in self.suspended_providers:
            await self.resume_provider(provider)
            logger.info("🔄 Provider auto-resumed", provider=provider)
    
    async def _auto_resume_agent(self, agent_id: str, duration_minutes: int):
        """Automatically resume an agent after duration"""
        
        await asyncio.sleep(duration_minutes * 60)
        
        if agent_id in self.suspended_agents:
            await self.resume_agent(agent_id)
            logger.info("🔄 Agent auto-resumed", agent_id=agent_id)
    
    async def resume_provider(self, provider: str):
        """Resume a suspended provider"""
        
        if provider in self.suspended_providers:
            self.suspended_providers.remove(provider)
            if provider in self.suspension_reasons:
                del self.suspension_reasons[provider]
            
            logger.info("✅ Provider resumed", provider=provider)
            
            await self._create_circuit_alert(
                "provider_resumed",
                "info",
                f"Provider {provider} resumed"
            )
    
    async def resume_agent(self, agent_id: str):
        """Resume a suspended agent"""
        
        if agent_id in self.suspended_agents:
            self.suspended_agents.remove(agent_id)
            if agent_id in self.suspension_reasons:
                del self.suspension_reasons[agent_id]
            
            logger.info("✅ Agent resumed", agent_id=agent_id)
            
            await self._create_circuit_alert(
                "agent_resumed",
                "info",
                f"Agent {agent_id} resumed"
            )
    
    async def emergency_override(self, override_code: str, duration_minutes: int = 60):
        """Emergency override to temporarily disable circuit breaker"""
        
        # Simple override validation (in production, use proper auth)
        valid_codes = ["EMERGENCY_OVERRIDE", "BUDGET_OVERRIDE", "ADMIN_OVERRIDE"]
        
        if override_code not in valid_codes:
            logger.warning("❌ Invalid override code attempted", code=override_code[:4] + "***")
            return False
        
        # Store override
        override_id = f"override_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.override_codes[override_id] = {
            "code": override_code,
            "activated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat(),
            "duration_minutes": duration_minutes
        }
        
        # Temporarily close circuit
        await self._close_circuit(f"Emergency override: {override_code}")
        
        # Auto-expire override
        asyncio.create_task(self._expire_override(override_id, duration_minutes))
        
        logger.critical("🚨 Emergency override activated",
                       code=override_code,
                       duration_minutes=duration_minutes,
                       override_id=override_id)
        
        return True
    
    async def _expire_override(self, override_id: str, duration_minutes: int):
        """Expire an emergency override"""
        
        await asyncio.sleep(duration_minutes * 60)
        
        if override_id in self.override_codes:
            del self.override_codes[override_id]
            logger.info("⏰ Emergency override expired", override_id=override_id)
            
            # Re-evaluate circuit state
            await self.periodic_check()
    
    async def periodic_check(self):
        """Periodic check for circuit breaker state transitions"""
        
        try:
            current_time = datetime.utcnow()
            
            # Check if we should transition from OPEN to HALF_OPEN
            if (self.circuit_state == CircuitState.OPEN and 
                self.last_failure_time and
                (current_time - self.last_failure_time).total_seconds() > self.recovery_timeout):
                
                await self._half_open_circuit("Recovery timeout reached")
            
            # Check current budget status
            budget_status = await budget_monitor.get_budget_status_summary()
            
            # If overall status is healthy and circuit is open, try half-open
            if (budget_status["overall_status"] == "healthy" and 
                self.circuit_state == CircuitState.OPEN):
                await self._half_open_circuit("Budget status improved")
            
            # Check for provider suspensions based on credit utilization
            for provider in budget_status.get("critical_providers", []):
                if provider not in self.suspended_providers:
                    await self.suspend_provider(
                        provider, 
                        SuspensionReason.PROVIDER_CREDITS_EXHAUSTED,
                        duration_minutes=60  # 1 hour suspension
                    )
        
        except Exception as e:
            logger.error("❌ Failed periodic circuit check", error=str(e))
    
    async def get_circuit_status(self) -> Dict[str, Any]:
        """Get comprehensive circuit breaker status"""
        
        return {
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "suspended_providers": list(self.suspended_providers),
            "suspended_agents": list(self.suspended_agents),
            "suspension_reasons": self.suspension_reasons,
            "active_overrides": len(self.override_codes),
            "health_status": "healthy" if self.circuit_state == CircuitState.CLOSED else "impaired",
            "next_check": (datetime.utcnow() + timedelta(seconds=self.check_interval)).isoformat()
        }
    
    async def _create_circuit_alert(self, alert_type: str, severity: str, message: str):
        """Create a circuit breaker alert"""
        
        try:
            from ..models.cost_tracking import CostAlert
            
            async with get_async_session() as db:
                alert = CostAlert(
                    alert_type=f"circuit_{alert_type}",
                    severity=severity,
                    current_value=Decimal("0"),
                    threshold_value=Decimal("0"), 
                    message=f"Circuit Breaker: {message}"
                )
                db.add(alert)
                await db.commit()
                
        except Exception as e:
            logger.error("❌ Failed to create circuit alert", error=str(e))
    
    async def start_monitoring(self):
        """Start the continuous monitoring loop"""
        
        logger.info("🚦 Starting circuit breaker monitoring")
        
        while True:
            try:
                await self.periodic_check()
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error("❌ Circuit breaker monitoring error", error=str(e))
                await asyncio.sleep(self.check_interval)


# Global circuit breaker instance
circuit_breaker = CircuitBreakerService()


# Helper decorator for API routes
def circuit_breaker_check(provider: str = "openai"):
    """Decorator to check circuit breaker before API calls"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract agent_id from kwargs if available
            agent_id = kwargs.get("agent_id")
            
            # Check if request should be blocked
            should_block, block_reason = await circuit_breaker.check_should_block_request(
                provider=provider,
                agent_id=agent_id
            )
            
            if should_block:
                logger.warning("🚫 Request blocked by circuit breaker", 
                             provider=provider, 
                             agent_id=agent_id,
                             reason=block_reason)
                
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "circuit_breaker_active",
                        "message": "Request blocked due to budget limits",
                        "details": block_reason
                    }
                )
            
            # Proceed with original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator