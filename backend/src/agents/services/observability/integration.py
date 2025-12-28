"""
Observability Integration - End-to-end integration with AutoGen orchestrator
Provides seamless observability across all AutoGen components.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

import structlog

from .telemetry import (
    TelemetryContext,
    ObservabilityEvent,
    initialize_telemetry,
    get_telemetry
)
from .metrics_collector import (
    initialize_metrics_collector,
    get_metrics_collector
)

logger = structlog.get_logger()


class ObservabilityIntegration:
    """Complete observability integration for AutoGen"""
    
    def __init__(
        self,
        service_name: str = "convergio-autogen",
        telemetry_endpoint: Optional[str] = None,
        metrics_window_minutes: int = 60
    ):
        # Initialize telemetry
        self.telemetry = initialize_telemetry(service_name, telemetry_endpoint)
        
        # Initialize metrics collector
        self.metrics = initialize_metrics_collector(metrics_window_minutes)
        
        # Register event handlers
        self._register_event_handlers()
        
        # Start metrics collector
        asyncio.create_task(self.metrics.start())
        
        logger.info("🔍 Observability integration initialized")
    
    def _register_event_handlers(self):
        """Register telemetry event handlers for metrics collection"""
        
        # Conversation events
        self.telemetry.add_event_handler(
            ObservabilityEvent.CONVERSATION_END,
            self._handle_conversation_end
        )
        
        # Agent events
        self.telemetry.add_event_handler(
            ObservabilityEvent.AGENT_RESPONSE,
            self._handle_agent_response
        )
        
        # Cost events
        self.telemetry.add_event_handler(
            ObservabilityEvent.COST_TRACKED,
            self._handle_cost_tracked
        )
        
        # Budget events
        self.telemetry.add_event_handler(
            ObservabilityEvent.BUDGET_WARNING,
            self._handle_budget_warning
        )
        
        self.telemetry.add_event_handler(
            ObservabilityEvent.BUDGET_EXCEEDED,
            self._handle_budget_exceeded
        )
        
        # Performance events
        self.telemetry.add_event_handler(
            ObservabilityEvent.PERFORMANCE_DEGRADATION,
            self._handle_performance_degradation
        )
        
        # Selection events
        self.telemetry.add_event_handler(
            ObservabilityEvent.SELECTION_DECISION,
            self._handle_selection_decision
        )
        
        # Memory events
        self.telemetry.add_event_handler(
            ObservabilityEvent.MEMORY_UPDATE,
            self._handle_memory_update
        )
    
    def _handle_conversation_end(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle conversation end event"""
        self.metrics.record_conversation_metrics(
            conversation_id=context.conversation_id,
            duration_seconds=attributes.get("duration", 0),
            status=attributes.get("status", "completed"),
            user_type=attributes.get("user_type", "standard"),
            workflow_type=attributes.get("workflow_type", "general")
        )
    
    def _handle_agent_response(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle agent response event"""
        self.metrics.record_agent_metrics(
            agent_name=attributes.get("agent.name", "unknown"),
            response_time_seconds=attributes.get("response_time", 0),
            status=attributes.get("status", "success")
        )
    
    def _handle_cost_tracked(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle cost tracked event"""
        self.metrics.record_cost_metrics(
            cost_usd=attributes.get("cost_usd", 0),
            tokens=attributes.get("tokens", 0),
            model=attributes.get("model", "unknown"),
            agent=attributes.get("agent.name", "unknown")
        )
    
    def _handle_budget_warning(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle budget warning event"""
        self.metrics.update_budget_metrics(
            daily_cost_usd=attributes.get("current_cost_usd", 0),
            daily_limit_usd=attributes.get("limit_usd", 50)
        )
        
        logger.warning(
            "⚠️ Budget warning triggered",
            remaining_usd=attributes.get("remaining_usd", 0),
            limit_usd=attributes.get("limit_usd", 50)
        )
    
    def _handle_budget_exceeded(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle budget exceeded event"""
        logger.error(
            "🚨 Budget exceeded!",
            current_cost_usd=attributes.get("current_cost_usd", 0),
            limit_usd=attributes.get("limit_usd", 50)
        )
    
    def _handle_performance_degradation(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle performance degradation event"""
        logger.warning(
            "⚡ Performance degradation detected",
            issue_type=attributes.get("performance.issue"),
            metric_value=attributes.get("metric.value"),
            threshold=attributes.get("metric.threshold")
        )
    
    def _handle_selection_decision(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle selection decision event"""
        self.metrics.record_selection_metrics(
            accuracy_score=attributes.get("selection.confidence", 0),
            selection_method=attributes.get("selection.reason", "unknown")
        )
    
    def _handle_memory_update(
        self,
        event: ObservabilityEvent,
        context: TelemetryContext,
        attributes: Dict[str, Any]
    ):
        """Handle memory update event"""
        self.metrics.record_memory_metrics(
            operation=attributes.get("operation", "unknown"),
            memory_type=attributes.get("memory.type", "unknown"),
            size_bytes=attributes.get("size.bytes", 0)
        )
    
    def create_context(
        self,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> TelemetryContext:
        """Create telemetry context"""
        return TelemetryContext(
            conversation_id=conversation_id,
            user_id=user_id,
            **kwargs
        )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get complete health status"""
        metrics_health = self.metrics.get_health_status()
        telemetry_metrics = self.telemetry.export_metrics()
        
        return {
            "status": "healthy" if metrics_health["status"] == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics_health,
            "telemetry": telemetry_metrics,
            "active_alerts": metrics_health.get("active_alerts", [])
        }
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        dashboard_metrics = self.metrics.get_dashboard_metrics()
        
        # Get aggregated metrics for different periods
        conversation_5m = await self.metrics.get_aggregated_metrics("conversation_duration", "5m")
        agent_5m = await self.metrics.get_aggregated_metrics("agent_response_time", "5m")
        cost_1h = await self.metrics.get_aggregated_metrics("cost_per_turn", "1h")
        
        return {
            "summary": dashboard_metrics,
            "trends": {
                "conversations_5m": [
                    {
                        "period": m.period,
                        "count": m.count,
                        "avg_duration": m.mean,
                        "p95_duration": m.p95
                    }
                    for m in conversation_5m
                ],
                "agents_5m": [
                    {
                        "agent": m.labels.get("agent", "unknown"),
                        "avg_response_time": m.mean,
                        "p95_response_time": m.p95,
                        "invocations": m.count
                    }
                    for m in agent_5m
                ],
                "cost_1h": [
                    {
                        "model": m.labels.get("model", "unknown"),
                        "avg_cost": m.mean,
                        "total_cost": m.sum,
                        "turns": m.count
                    }
                    for m in cost_1h
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return self.metrics.export_prometheus_metrics()
    
    async def shutdown(self):
        """Shutdown observability systems"""
        await self.metrics.stop()
        self.telemetry.shutdown()
        logger.info("Observability integration shutdown complete")


def observe_conversation(func):
    """Decorator to automatically observe conversations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract context from arguments
        self = args[0] if args else None
        kwargs.get("message", "")
        user_id = kwargs.get("user_id", "unknown")
        conversation_id = kwargs.get("conversation_id", str(datetime.utcnow().timestamp()))
        
        # Get observability integration
        observability = getattr(self, "observability", None)
        if not observability:
            # No observability, run function normally
            return await func(*args, **kwargs)
        
        # Create context
        context = observability.create_context(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        # Trace conversation
        with observability.telemetry.trace_conversation(context):
            try:
                # Update active conversations metric
                observability.metrics.update_performance_metrics(
                    active_conversations=observability.metrics.active_conversations._value.get() + 1,
                    queue_sizes={},
                    error_counts={}
                )
                
                # Run actual function
                result = await func(*args, **kwargs)
                
                # Record success
                if hasattr(result, "cost_breakdown"):
                    observability.telemetry.record_cost_metrics(
                        cost_usd=result.cost_breakdown.get("total_cost", 0),
                        tokens=result.cost_breakdown.get("total_tokens", 0),
                        model=result.cost_breakdown.get("model", "unknown"),
                        context=context
                    )
                
                return result
                
            finally:
                # Update active conversations metric
                observability.metrics.update_performance_metrics(
                    active_conversations=max(0, observability.metrics.active_conversations._value.get() - 1),
                    queue_sizes={},
                    error_counts={}
                )
    
    return wrapper


def observe_agent(func):
    """Decorator to automatically observe agent invocations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract context
        self = args[0] if args else None
        agent_name = getattr(self, "name", "unknown")
        
        # Get observability
        telemetry = get_telemetry()
        metrics = get_metrics_collector()
        
        if not telemetry or not metrics:
            return await func(*args, **kwargs)
        
        # Create context
        context = TelemetryContext(
            conversation_id=kwargs.get("conversation_id", "unknown"),
            user_id=kwargs.get("user_id", "unknown"),
            agent_name=agent_name
        )
        
        # Trace agent invocation
        with telemetry.trace_agent_invocation(context):
            result = await func(*args, **kwargs)
            return result
    
    return wrapper


def observe_tool(tool_name: str):
    """Decorator to automatically observe tool calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get observability
            telemetry = get_telemetry()
            
            if not telemetry:
                return await func(*args, **kwargs)
            
            # Create context
            context = TelemetryContext(
                conversation_id=kwargs.get("conversation_id", "unknown"),
                user_id=kwargs.get("user_id", "unknown"),
                agent_name=kwargs.get("agent_name", "unknown")
            )
            
            # Trace tool call
            with telemetry.trace_tool_call(tool_name, context):
                result = await func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


def observe_workflow(workflow_id: str):
    """Decorator to automatically observe workflow execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get observability
            telemetry = get_telemetry()
            
            if not telemetry:
                return await func(*args, **kwargs)
            
            # Create context
            context = TelemetryContext(
                conversation_id=kwargs.get("conversation_id", "unknown"),
                user_id=kwargs.get("user_id", "unknown"),
                workflow_id=workflow_id
            )
            
            # Trace workflow
            with telemetry.trace_workflow(workflow_id, context):
                result = await func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


# Global observability instance
_observability: Optional[ObservabilityIntegration] = None


def initialize_observability(
    service_name: str = "convergio-autogen",
    telemetry_endpoint: Optional[str] = None,
    metrics_window_minutes: int = 60
) -> ObservabilityIntegration:
    """Initialize global observability"""
    global _observability
    _observability = ObservabilityIntegration(
        service_name,
        telemetry_endpoint,
        metrics_window_minutes
    )
    return _observability


def get_observability() -> Optional[ObservabilityIntegration]:
    """Get global observability instance"""
    return _observability


__all__ = [
    "ObservabilityIntegration",
    "initialize_observability",
    "get_observability",
    "observe_conversation",
    "observe_agent",
    "observe_tool",
    "observe_workflow"
]