"""
Cost Circuit Breaker - Advanced cost control with circuit breaker pattern
Implements circuit breaker, budget alarms, and rate limiting for cost management
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import structlog

import redis.asyncio as redis

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class BudgetLevel(Enum):
    """Budget alert levels"""
    HEALTHY = "healthy"      # < 50% budget
    MODERATE = "moderate"    # 50-70% budget
    WARNING = "warning"      # 70-85% budget
    CRITICAL = "critical"    # 85-95% budget
    EXCEEDED = "exceeded"    # > 100% budget


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5          # Number of failures to trip
    success_threshold: int = 3          # Successes needed to close from half-open
    timeout_seconds: int = 60           # Time before trying half-open
    budget_limit_usd: float = 50.0      # Daily budget limit
    conversation_limit_usd: float = 5.0  # Per-conversation limit
    turn_limit_usd: float = 0.5         # Per-turn limit
    spike_threshold_factor: float = 3.0  # Factor for cost spike detection
    
    # Alert thresholds
    warning_threshold: float = 0.7      # 70% of budget
    critical_threshold: float = 0.85    # 85% of budget
    
    # Rate limiting
    max_turns_per_minute: int = 10
    max_conversations_per_hour: int = 20
    max_daily_conversations: int = 100


@dataclass
class CostMetrics:
    """Metrics for cost tracking"""
    total_cost: float = 0.0
    turn_count: int = 0
    conversation_count: int = 0
    failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    cost_history: deque = field(default_factory=lambda: deque(maxlen=100))
    turn_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))


class CostCircuitBreaker:
    """Advanced cost control with circuit breaker pattern"""
    
    def __init__(
        self,
        config: Optional[CircuitBreakerConfig] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        self.config = config or CircuitBreakerConfig()
        self.redis = redis_client
        self.state = CircuitState.CLOSED
        self.metrics = CostMetrics()
        self.state_changed_at = datetime.utcnow()
        self.callbacks: Dict[str, List[Callable]] = {
            "on_open": [],
            "on_close": [],
            "on_half_open": [],
            "on_budget_warning": [],
            "on_budget_critical": [],
            "on_budget_exceeded": [],
            "on_cost_spike": []
        }
        self.rate_limiters: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize circuit breaker and restore state"""
        if self.redis:
            # Restore state from Redis
            await self._restore_state()
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_recovery())
        asyncio.create_task(self._monitor_budgets())
        
        logger.info(
            "🔌 Cost Circuit Breaker initialized",
            state=self.state.value,
            budget_limit=self.config.budget_limit_usd
        )
    
    async def check_cost(
        self,
        cost_usd: float,
        conversation_id: str,
        turn_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if cost is allowed through circuit breaker
        Returns (allowed, status_info)
        """
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            return False, {
                "status": "blocked",
                "reason": "Circuit breaker is OPEN",
                "state": self.state.value,
                "retry_after": self._get_retry_after()
            }
        
        # Check rate limiting
        rate_limit_ok, rate_limit_info = await self._check_rate_limits(conversation_id)
        if not rate_limit_ok:
            return False, {
                "status": "rate_limited",
                "reason": rate_limit_info["reason"],
                "retry_after": rate_limit_info.get("retry_after")
            }
        
        # Check budget limits
        budget_ok, budget_info = await self._check_budget_limits(cost_usd, conversation_id)
        if not budget_ok:
            # Trip circuit breaker
            await self._trip_breaker(budget_info["reason"])
            return False, {
                "status": "budget_exceeded",
                "reason": budget_info["reason"],
                "budget_info": budget_info
            }
        
        # Check for cost spikes
        spike_detected, spike_info = await self._check_cost_spike(cost_usd)
        if spike_detected:
            self.metrics.failures += 1
            
            # Trip if too many spikes
            if self.metrics.failures >= self.config.failure_threshold:
                await self._trip_breaker("Too many cost spikes detected")
                return False, {
                    "status": "spike_protection",
                    "reason": spike_info["reason"],
                    "spike_info": spike_info
                }
            
            # Warn but allow
            await self._notify_callbacks("on_cost_spike", spike_info)
        
        # Record successful cost check
        await self._record_success(cost_usd, conversation_id, turn_id)
        
        # Check if we should close from half-open
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.failures == 0 and len(self.metrics.cost_history) >= self.config.success_threshold:
                await self._close_breaker()
        
        return True, {
            "status": "allowed",
            "state": self.state.value,
            "metrics": {
                "total_cost": self.metrics.total_cost,
                "turn_count": self.metrics.turn_count,
                "budget_usage": self.metrics.total_cost / self.config.budget_limit_usd,
                "budget_level": self._get_budget_level().value
            }
        }
    
    async def _check_rate_limits(self, conversation_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limiting constraints"""
        now = datetime.utcnow()
        
        # Per-minute turn rate limit
        recent_turns = [
            ts for ts in self.metrics.turn_timestamps
            if (now - ts).total_seconds() < 60
        ]
        
        if len(recent_turns) >= self.config.max_turns_per_minute:
            return False, {
                "reason": f"Turn rate limit exceeded ({self.config.max_turns_per_minute}/min)",
                "retry_after": 60 - (now - recent_turns[0]).total_seconds()
            }
        
        # Per-hour conversation rate limit
        hour_key = f"conv_hour:{now.strftime('%Y%m%d%H')}"
        if self.redis:
            conv_count = await self.redis.incr(hour_key)
            await self.redis.expire(hour_key, 3600)
            
            if conv_count > self.config.max_conversations_per_hour:
                return False, {
                    "reason": f"Hourly conversation limit exceeded ({self.config.max_conversations_per_hour}/hour)",
                    "retry_after": 3600 - (now.minute * 60 + now.second)
                }
        
        return True, {"status": "ok"}
    
    async def _check_budget_limits(
        self,
        cost_usd: float,
        conversation_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check budget constraints"""
        
        # Check turn cost limit
        if cost_usd > self.config.turn_limit_usd:
            return False, {
                "reason": f"Turn cost ${cost_usd} exceeds limit ${self.config.turn_limit_usd}",
                "limit_type": "turn",
                "cost": cost_usd,
                "limit": self.config.turn_limit_usd
            }
        
        # Check conversation cost limit
        if self.redis:
            conv_key = f"conversation_cost:{conversation_id}"
            conv_cost = await self.redis.get(conv_key)
            conv_cost = float(conv_cost or 0) + cost_usd
            
            if conv_cost > self.config.conversation_limit_usd:
                return False, {
                    "reason": f"Conversation cost ${conv_cost} exceeds limit ${self.config.conversation_limit_usd}",
                    "limit_type": "conversation",
                    "cost": conv_cost,
                    "limit": self.config.conversation_limit_usd
                }
        
        # Check daily budget limit
        projected_cost = self.metrics.total_cost + cost_usd
        if projected_cost > self.config.budget_limit_usd:
            return False, {
                "reason": f"Daily budget ${self.config.budget_limit_usd} would be exceeded",
                "limit_type": "daily",
                "current_cost": self.metrics.total_cost,
                "projected_cost": projected_cost,
                "limit": self.config.budget_limit_usd
            }
        
        # Check budget alert levels
        budget_level = self._get_budget_level(projected_cost)
        
        if budget_level == BudgetLevel.CRITICAL:
            await self._notify_callbacks("on_budget_critical", {
                "current_cost": self.metrics.total_cost,
                "projected_cost": projected_cost,
                "budget_limit": self.config.budget_limit_usd,
                "usage_percentage": (projected_cost / self.config.budget_limit_usd) * 100
            })
        elif budget_level == BudgetLevel.WARNING:
            await self._notify_callbacks("on_budget_warning", {
                "current_cost": self.metrics.total_cost,
                "projected_cost": projected_cost,
                "budget_limit": self.config.budget_limit_usd,
                "usage_percentage": (projected_cost / self.config.budget_limit_usd) * 100
            })
        
        return True, {
            "status": "ok",
            "budget_level": budget_level.value,
            "remaining_budget": self.config.budget_limit_usd - projected_cost
        }
    
    async def _check_cost_spike(self, cost_usd: float) -> Tuple[bool, Dict[str, Any]]:
        """Detect unusual cost spikes"""
        
        if len(self.metrics.cost_history) < 5:
            # Not enough history
            return False, {"status": "insufficient_history"}
        
        # Calculate moving average
        recent_costs = list(self.metrics.cost_history)[-10:]
        avg_cost = sum(recent_costs) / len(recent_costs)
        
        # Check for spike
        if cost_usd > avg_cost * self.config.spike_threshold_factor:
            return True, {
                "reason": f"Cost spike detected: ${cost_usd} > ${avg_cost * self.config.spike_threshold_factor}",
                "current_cost": cost_usd,
                "average_cost": avg_cost,
                "spike_factor": cost_usd / avg_cost
            }
        
        return False, {"status": "normal"}
    
    async def _trip_breaker(self, reason: str):
        """Trip the circuit breaker to OPEN state"""
        
        old_state = self.state
        self.state = CircuitState.OPEN
        self.state_changed_at = datetime.utcnow()
        self.metrics.last_failure_time = datetime.utcnow()
        
        logger.warning(
            "⚡ Circuit breaker tripped",
            old_state=old_state.value,
            new_state=self.state.value,
            reason=reason
        )
        
        # Persist state
        await self._persist_state()
        
        # Notify callbacks
        await self._notify_callbacks("on_open", {
            "reason": reason,
            "timestamp": self.state_changed_at.isoformat(),
            "metrics": {
                "total_cost": self.metrics.total_cost,
                "failures": self.metrics.failures
            }
        })
    
    async def _close_breaker(self):
        """Close the circuit breaker to CLOSED state"""
        
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.state_changed_at = datetime.utcnow()
        self.metrics.failures = 0
        
        logger.info(
            "✅ Circuit breaker closed",
            old_state=old_state.value,
            new_state=self.state.value
        )
        
        # Persist state
        await self._persist_state()
        
        # Notify callbacks
        await self._notify_callbacks("on_close", {
            "timestamp": self.state_changed_at.isoformat(),
            "recovery_time": (datetime.utcnow() - self.metrics.last_failure_time).total_seconds()
                if self.metrics.last_failure_time else 0
        })
    
    async def _half_open_breaker(self):
        """Transition to HALF_OPEN state for testing"""
        
        self.state = CircuitState.HALF_OPEN
        self.state_changed_at = datetime.utcnow()
        self.metrics.failures = 0  # Reset for testing
        
        logger.info("🔄 Circuit breaker half-open for testing")
        
        # Persist state
        await self._persist_state()
        
        # Notify callbacks
        await self._notify_callbacks("on_half_open", {
            "timestamp": self.state_changed_at.isoformat()
        })
    
    async def _record_success(
        self,
        cost_usd: float,
        conversation_id: str,
        turn_id: Optional[str]
    ):
        """Record successful cost check"""
        
        self.metrics.total_cost += cost_usd
        self.metrics.turn_count += 1
        self.metrics.cost_history.append(cost_usd)
        self.metrics.turn_timestamps.append(datetime.utcnow())
        self.metrics.last_success_time = datetime.utcnow()
        
        # Update conversation cost
        if self.redis:
            conv_key = f"conversation_cost:{conversation_id}"
            await self.redis.incrbyfloat(conv_key, cost_usd)
            await self.redis.expire(conv_key, 86400)  # 24 hours
            
            # Update daily cost
            daily_key = f"daily_cost:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis.incrbyfloat(daily_key, cost_usd)
            await self.redis.expire(daily_key, 86400)
    
    def _get_budget_level(self, cost: Optional[float] = None) -> BudgetLevel:
        """Determine current budget alert level"""
        
        if cost is None:
            cost = self.metrics.total_cost
        
        usage = cost / self.config.budget_limit_usd
        
        if usage >= 1.0:
            return BudgetLevel.EXCEEDED
        elif usage >= self.config.critical_threshold:
            return BudgetLevel.CRITICAL
        elif usage >= self.config.warning_threshold:
            return BudgetLevel.WARNING
        elif usage >= 0.5:
            return BudgetLevel.MODERATE
        else:
            return BudgetLevel.HEALTHY
    
    def _get_retry_after(self) -> float:
        """Get seconds until circuit might close"""
        
        if self.state != CircuitState.OPEN:
            return 0
        
        elapsed = (datetime.utcnow() - self.state_changed_at).total_seconds()
        remaining = max(0, self.config.timeout_seconds - elapsed)
        
        return remaining
    
    async def _monitor_recovery(self):
        """Monitor for automatic recovery from OPEN state"""
        
        while True:
            try:
                if self.state == CircuitState.OPEN:
                    elapsed = (datetime.utcnow() - self.state_changed_at).total_seconds()
                    
                    if elapsed >= self.config.timeout_seconds:
                        await self._half_open_breaker()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error("Error in recovery monitor", error=str(e))
                await asyncio.sleep(30)
    
    async def _monitor_budgets(self):
        """Monitor budget levels and send alerts"""
        
        while True:
            try:
                budget_level = self._get_budget_level()
                
                if budget_level == BudgetLevel.EXCEEDED:
                    await self._notify_callbacks("on_budget_exceeded", {
                        "total_cost": self.metrics.total_cost,
                        "budget_limit": self.config.budget_limit_usd,
                        "overage": self.metrics.total_cost - self.config.budget_limit_usd
                    })
                    
                    # Auto-trip if exceeded
                    if self.state == CircuitState.CLOSED:
                        await self._trip_breaker("Daily budget exceeded")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error in budget monitor", error=str(e))
                await asyncio.sleep(60)
    
    async def _persist_state(self):
        """Persist circuit breaker state to Redis"""
        
        if self.redis:
            import json
            state_data = {
                "state": self.state.value,
                "state_changed_at": self.state_changed_at.isoformat(),
                "metrics": {
                    "total_cost": self.metrics.total_cost,
                    "turn_count": self.metrics.turn_count,
                    "failures": self.metrics.failures
                }
            }
            
            await self.redis.setex(
                "circuit_breaker:state",
                86400,  # 24 hours
                json.dumps(state_data)
            )
    
    async def _restore_state(self):
        """Restore circuit breaker state from Redis"""
        
        if self.redis:
            import json
            state_data = await self.redis.get("circuit_breaker:state")
            
            if state_data:
                data = json.loads(state_data)
                self.state = CircuitState(data["state"])
                self.state_changed_at = datetime.fromisoformat(data["state_changed_at"])
                self.metrics.total_cost = data["metrics"]["total_cost"]
                self.metrics.turn_count = data["metrics"]["turn_count"]
                self.metrics.failures = data["metrics"]["failures"]
                
                logger.info(
                    "Circuit breaker state restored",
                    state=self.state.value,
                    total_cost=self.metrics.total_cost
                )
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for circuit breaker events"""
        
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    async def _notify_callbacks(self, event: str, data: Dict[str, Any]):
        """Notify registered callbacks"""
        
        for callback in self.callbacks.get(event, []):
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event}", error=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        
        return {
            "state": self.state.value,
            "state_changed_at": self.state_changed_at.isoformat(),
            "metrics": {
                "total_cost": self.metrics.total_cost,
                "turn_count": self.metrics.turn_count,
                "conversation_count": self.metrics.conversation_count,
                "failures": self.metrics.failures,
                "budget_usage": self.metrics.total_cost / self.config.budget_limit_usd,
                "budget_level": self._get_budget_level().value
            },
            "config": {
                "budget_limit_usd": self.config.budget_limit_usd,
                "conversation_limit_usd": self.config.conversation_limit_usd,
                "turn_limit_usd": self.config.turn_limit_usd,
                "warning_threshold": self.config.warning_threshold,
                "critical_threshold": self.config.critical_threshold
            },
            "retry_after": self._get_retry_after() if self.state == CircuitState.OPEN else None
        }
    
    async def reset_daily_metrics(self):
        """Reset daily metrics (call at midnight)"""
        
        self.metrics = CostMetrics()
        self.state = CircuitState.CLOSED
        self.state_changed_at = datetime.utcnow()
        
        logger.info("Daily metrics reset")
        
        await self._persist_state()


__all__ = [
    "CostCircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "BudgetLevel",
    "CostMetrics"
]