"""
Convergio Observability - OpenTelemetry integration for comprehensive monitoring
Implements distributed tracing, metrics collection, and structured logging for AutoGen workflows.
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import traceback

import structlog
from opentelemetry import trace, metrics, baggage
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
try:
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
except Exception:
    LoggingInstrumentor = None  # type: ignore
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = structlog.get_logger()


class ObservabilityEvent(Enum):
    """Types of observability events"""
    CONVERSATION_START = "conversation.start"
    CONVERSATION_END = "conversation.end"
    AGENT_INVOCATION = "agent.invocation"
    AGENT_RESPONSE = "agent.response"
    TOOL_CALL = "tool.call"
    TOOL_RESULT = "tool.result"
    # Plan-aligned explicit events
    DECISION_MADE = "decision.made"
    TOOL_INVOKED = "tool.invoked"
    BUDGET_EVENT = "budget.event"
    WORKFLOW_START = "workflow.start"
    WORKFLOW_STEP = "workflow.step"
    WORKFLOW_END = "workflow.end"
    COST_TRACKED = "cost.tracked"
    BUDGET_WARNING = "budget.warning"
    BUDGET_EXCEEDED = "budget.exceeded"
    MEMORY_ACCESS = "memory.access"
    MEMORY_UPDATE = "memory.update"
    SELECTION_DECISION = "selection.decision"
    STREAMING_START = "streaming.start"
    STREAMING_CHUNK = "streaming.chunk"
    STREAMING_END = "streaming.end"
    ERROR_OCCURRED = "error.occurred"
    PERFORMANCE_DEGRADATION = "performance.degradation"
    SECURITY_EVENT = "security.event"
    HITL_APPROVAL_REQUIRED = "hitl.approval_required"
    HITL_APPROVAL_GRANTED = "hitl.approval_granted"
    HITL_APPROVAL_DENIED = "hitl.approval_denied"


@dataclass
class TelemetryContext:
    """Context for telemetry operations"""
    conversation_id: str
    user_id: str
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    agent_name: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    baggage: Dict[str, str] = field(default_factory=dict)


class ConvergioTelemetry:
    """Comprehensive telemetry system for Convergio AutoGen"""
    
    def __init__(self, service_name: str = "convergio-autogen", endpoint: Optional[str] = None):
        self.service_name = service_name
        self.endpoint = endpoint or "localhost:4317"
        
        # Initialize OpenTelemetry
        self._init_tracing()
        self._init_metrics()
        self._init_logging()
        
        # Create metrics
        self._create_metrics()
        
        # Event handlers
        self.event_handlers: Dict[ObservabilityEvent, List[Callable]] = {}
        
        # Active spans tracking
        self.active_spans: Dict[str, Span] = {}
        
        logger.info(f"🔭 Telemetry initialized for {service_name} -> {self.endpoint}")
    
    def _init_tracing(self):
        """Initialize distributed tracing"""
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self.tracer_provider)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.endpoint,
            insecure=True
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        
        # Get tracer
        self.tracer = trace.get_tracer(self.service_name)
        
        # Propagator for distributed tracing
        self.propagator = TraceContextTextMapPropagator()
    
    def _init_metrics(self):
        """Initialize metrics collection"""
        resource = Resource.create({
            "service.name": self.service_name
        })
        
        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=self.endpoint, insecure=True),
            export_interval_millis=10000  # Export every 10 seconds
        )
        
        # Create meter provider
        self.meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(self.meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter(self.service_name)
    
    def _init_logging(self):
        """Initialize structured logging with tracing context"""
        try:
            if LoggingInstrumentor is not None:
                LoggingInstrumentor().instrument()
        except Exception:
            # Best-effort: continue without logging instrumentation in tests
            pass
        
        # Configure structlog to include trace context
        structlog.configure(
            processors=[
                self._add_trace_context,
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def _add_trace_context(self, logger, method_name, event_dict):
        """Add trace context to log entries"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
        return event_dict
    
    def _create_metrics(self):
        """Create metric instruments"""
        # Counters
        self.conversation_counter = self.meter.create_counter(
            "convergio.conversations.total",
            description="Total number of conversations",
            unit="1"
        )
        
        self.agent_invocation_counter = self.meter.create_counter(
            "convergio.agent.invocations",
            description="Number of agent invocations",
            unit="1"
        )
        
        self.tool_call_counter = self.meter.create_counter(
            "convergio.tool.calls",
            description="Number of tool calls",
            unit="1"
        )
        
        self.error_counter = self.meter.create_counter(
            "convergio.errors.total",
            description="Total number of errors",
            unit="1"
        )
        
        # Histograms
        self.conversation_duration_histogram = self.meter.create_histogram(
            "convergio.conversation.duration",
            description="Conversation duration in seconds",
            unit="s"
        )
        
        self.agent_response_time_histogram = self.meter.create_histogram(
            "convergio.agent.response_time",
            description="Agent response time in seconds",
            unit="s"
        )
        
        self.cost_histogram = self.meter.create_histogram(
            "convergio.cost.per_turn",
            description="Cost per conversation turn",
            unit="USD"
        )
        
        self.token_histogram = self.meter.create_histogram(
            "convergio.tokens.per_turn",
            description="Tokens used per turn",
            unit="1"
        )
        
        # UpDown Counters (gauges)
        self.active_conversations_gauge = self.meter.create_up_down_counter(
            "convergio.conversations.active",
            description="Number of active conversations",
            unit="1"
        )
        
        self.memory_usage_gauge = self.meter.create_up_down_counter(
            "convergio.memory.usage_bytes",
            description="Memory usage in bytes",
            unit="By"
        )
        
        self.budget_remaining_gauge = self.meter.create_up_down_counter(
            "convergio.budget.remaining",
            description="Remaining budget in USD",
            unit="USD"
        )
    
    @contextmanager
    def trace_conversation(self, context: TelemetryContext):
        """Trace a complete conversation"""
        attributes = {
            "conversation.id": context.conversation_id,
            "user.id": context.user_id,
            "session.id": context.session_id or "unknown",
            **context.attributes
        }
        
        with self.tracer.start_as_current_span(
            "conversation",
            kind=trace.SpanKind.SERVER,
            attributes=attributes
        ) as span:
            try:
                # Store span reference
                self.active_spans[context.conversation_id] = span
                
                # Set baggage for propagation
                for key, value in context.baggage.items():
                    baggage.set_baggage(key, value)
                
                # Record conversation start
                self.conversation_counter.add(1, attributes)
                self.active_conversations_gauge.add(1)
                
                # Emit event
                self._emit_event(ObservabilityEvent.CONVERSATION_START, context, attributes)
                
                start_time = time.time()
                yield span
                
                # Record duration
                duration = time.time() - start_time
                self.conversation_duration_histogram.record(duration, attributes)
                
                # Mark successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record error
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                self.error_counter.add(1, {**attributes, "error.type": type(e).__name__})
                self._emit_event(ObservabilityEvent.ERROR_OCCURRED, context, {
                    **attributes,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                raise
                
            finally:
                # Cleanup
                self.active_conversations_gauge.add(-1)
                self.active_spans.pop(context.conversation_id, None)
                self._emit_event(ObservabilityEvent.CONVERSATION_END, context, {
                    **attributes,
                    "duration": duration
                })
    
    @contextmanager
    def trace_agent_invocation(self, context: TelemetryContext):
        """Trace agent invocation"""
        attributes = {
            "agent.name": context.agent_name,
            "conversation.id": context.conversation_id,
            "user.id": context.user_id,
            **context.attributes
        }
        
        parent_span = self.active_spans.get(context.conversation_id)
        
        with self.tracer.start_as_current_span(
            f"agent.{context.agent_name}",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes,
            context=trace.set_span_in_context(parent_span) if parent_span else None
        ) as span:
            try:
                # Record invocation
                self.agent_invocation_counter.add(1, attributes)
                self._emit_event(ObservabilityEvent.AGENT_INVOCATION, context, attributes)
                
                start_time = time.time()
                yield span
                
                # Record response time
                response_time = time.time() - start_time
                self.agent_response_time_histogram.record(response_time, attributes)
                
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
                
            finally:
                self._emit_event(ObservabilityEvent.AGENT_RESPONSE, context, {
                    **attributes,
                    "response_time": response_time
                })
    
    @contextmanager
    def trace_tool_call(self, tool_name: str, context: TelemetryContext):
        """Trace tool call"""
        attributes = {
            "tool.name": tool_name,
            "agent.name": context.agent_name,
            "conversation.id": context.conversation_id,
            **context.attributes
        }
        
        with self.tracer.start_as_current_span(
            f"tool.{tool_name}",
            kind=trace.SpanKind.CLIENT,
            attributes=attributes
        ) as span:
            try:
                self.tool_call_counter.add(1, attributes)
                self._emit_event(ObservabilityEvent.TOOL_CALL, context, attributes)
                
                yield span
                
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
                
            finally:
                self._emit_event(ObservabilityEvent.TOOL_RESULT, context, attributes)
    
    @contextmanager
    def trace_workflow(self, workflow_id: str, context: TelemetryContext):
        """Trace workflow execution"""
        attributes = {
            "workflow.id": workflow_id,
            "conversation.id": context.conversation_id,
            "user.id": context.user_id,
            **context.attributes
        }
        
        with self.tracer.start_as_current_span(
            f"workflow.{workflow_id}",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        ) as span:
            try:
                self._emit_event(ObservabilityEvent.WORKFLOW_START, context, attributes)
                yield span
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
                
            finally:
                self._emit_event(ObservabilityEvent.WORKFLOW_END, context, attributes)
    
    def record_workflow_step(self, step_id: str, context: TelemetryContext):
        """Record workflow step execution"""
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(
                "workflow.step",
                attributes={
                    "step.id": step_id,
                    "workflow.id": context.workflow_id,
                    **context.attributes
                }
            )
        
        self._emit_event(ObservabilityEvent.WORKFLOW_STEP, context, {
            "step.id": step_id,
            "workflow.id": context.workflow_id
        })
    
    def record_cost_metrics(
        self,
        cost_usd: float,
        tokens: int,
        model: str,
        context: TelemetryContext
    ):
        """Record cost and token metrics"""
        attributes = {
            "model": model,
            "conversation.id": context.conversation_id,
            "agent.name": context.agent_name or "unknown"
        }
        
        # Record metrics
        self.cost_histogram.record(cost_usd, attributes)
        self.token_histogram.record(tokens, attributes)
        
        # Add span event
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(
                "cost.tracked",
                attributes={
                    "cost.usd": cost_usd,
                    "tokens": tokens,
                    "model": model
                }
            )
        
        self._emit_event(ObservabilityEvent.COST_TRACKED, context, {
            "cost_usd": cost_usd,
            "tokens": tokens,
            "model": model
        })

    def record_decision_made(self, details: Dict[str, Any], context: TelemetryContext):
        """Emit explicit decision_made event for UI alignment"""
        self._emit_event(ObservabilityEvent.DECISION_MADE, context, details)

    def record_tool_invoked(self, tool_name: str, context: TelemetryContext, attributes: Optional[Dict[str, Any]] = None):
        """Emit explicit tool_invoked event for UI alignment"""
        attrs = {"tool.name": tool_name}
        if attributes:
            attrs.update(attributes)
        self._emit_event(ObservabilityEvent.TOOL_INVOKED, context, attrs)

    def record_budget_event(self, status: str, remaining_usd: float, limit_usd: float, context: TelemetryContext):
        """Emit explicit budget_event for UI alignment"""
        self._emit_event(ObservabilityEvent.BUDGET_EVENT, context, {
            "status": status,
            "remaining_usd": remaining_usd,
            "limit_usd": limit_usd,
        })
    
    def record_budget_status(
        self,
        remaining_usd: float,
        limit_usd: float,
        status: str,
        context: TelemetryContext
    ):
        """Record budget status"""
        self.budget_remaining_gauge.add(remaining_usd - self.budget_remaining_gauge._value)
        
        attributes = {
            "remaining_usd": remaining_usd,
            "limit_usd": limit_usd,
            "status": status,
            "conversation.id": context.conversation_id
        }
        
        # Check for warnings/exceeded
        if status == "warning":
            self._emit_event(ObservabilityEvent.BUDGET_WARNING, context, attributes)
        elif status == "exceeded":
            self._emit_event(ObservabilityEvent.BUDGET_EXCEEDED, context, attributes)
        
        # Add span event
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(f"budget.{status}", attributes=attributes)
    
    def record_memory_operation(
        self,
        operation: str,
        memory_type: str,
        size_bytes: int,
        context: TelemetryContext
    ):
        """Record memory operations"""
        attributes = {
            "operation": operation,
            "memory.type": memory_type,
            "size.bytes": size_bytes,
            "conversation.id": context.conversation_id
        }
        
        # Update memory gauge
        if operation == "store":
            self.memory_usage_gauge.add(size_bytes)
            event = ObservabilityEvent.MEMORY_UPDATE
        else:
            event = ObservabilityEvent.MEMORY_ACCESS
        
        self._emit_event(event, context, attributes)
        
        # Add span event
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(f"memory.{operation}", attributes=attributes)
    
    def record_selection_decision(
        self,
        selected_agent: str,
        reason: str,
        confidence: float,
        context: TelemetryContext
    ):
        """Record agent selection decision"""
        attributes = {
            "selected.agent": selected_agent,
            "selection.reason": reason,
            "selection.confidence": confidence,
            "conversation.id": context.conversation_id
        }
        
        self._emit_event(ObservabilityEvent.SELECTION_DECISION, context, attributes)
        
        # Add span event
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event("agent.selected", attributes=attributes)
    
    def record_streaming_event(
        self,
        event_type: str,
        chunk_size: Optional[int] = None,
        context: Optional[TelemetryContext] = None
    ):
        """Record streaming events"""
        if event_type == "start":
            event = ObservabilityEvent.STREAMING_START
        elif event_type == "chunk":
            event = ObservabilityEvent.STREAMING_CHUNK
        else:
            event = ObservabilityEvent.STREAMING_END
        
        attributes = {
            "streaming.event": event_type,
            "chunk.size": chunk_size or 0
        }
        
        if context:
            attributes["conversation.id"] = context.conversation_id
        
        self._emit_event(event, context, attributes)
    
    def record_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
        context: TelemetryContext
    ):
        """Record security events"""
        attributes = {
            "security.event": event_type,
            "security.severity": severity,
            "conversation.id": context.conversation_id,
            **details
        }
        
        self._emit_event(ObservabilityEvent.SECURITY_EVENT, context, attributes)
        
        # Add span event with high priority
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(f"security.{event_type}", attributes=attributes)
            if severity == "critical":
                span.set_attribute("security.critical", True)
    
    def record_hitl_event(
        self,
        event_type: str,
        request_id: str,
        context: TelemetryContext
    ):
        """Record human-in-the-loop events"""
        if event_type == "required":
            event = ObservabilityEvent.HITL_APPROVAL_REQUIRED
        elif event_type == "granted":
            event = ObservabilityEvent.HITL_APPROVAL_GRANTED
        else:
            event = ObservabilityEvent.HITL_APPROVAL_DENIED
        
        attributes = {
            "hitl.event": event_type,
            "hitl.request_id": request_id,
            "conversation.id": context.conversation_id
        }
        
        self._emit_event(event, context, attributes)
    
    def record_performance_issue(
        self,
        issue_type: str,
        metric_value: float,
        threshold: float,
        context: TelemetryContext
    ):
        """Record performance degradation"""
        attributes = {
            "performance.issue": issue_type,
            "metric.value": metric_value,
            "metric.threshold": threshold,
            "conversation.id": context.conversation_id
        }
        
        self._emit_event(ObservabilityEvent.PERFORMANCE_DEGRADATION, context, attributes)
        
        # Add span event
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event("performance.degradation", attributes=attributes)
            span.set_attribute("performance.degraded", True)
    
    def add_event_handler(self, event: ObservabilityEvent, handler: Callable):
        """Add custom event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    def _emit_event(
        self,
        event: ObservabilityEvent,
        context: Optional[TelemetryContext],
        attributes: Dict[str, Any]
    ):
        """Emit observability event to handlers"""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(event, context, attributes)
            except Exception as e:
                logger.error(f"Event handler failed for {event.value}", error=str(e))
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context for propagation"""
        carrier = {}
        self.propagator.inject(carrier)
        return carrier
    
    def set_trace_context(self, carrier: Dict[str, str]):
        """Set trace context from propagation"""
        ctx = self.propagator.extract(carrier)
        trace.set_span_in_context(trace.get_current_span(), ctx)
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export current metrics snapshot"""
        return {
            "conversations": {
                "total": self.conversation_counter._value,
                "active": self.active_conversations_gauge._value
            },
            "agents": {
                "invocations": self.agent_invocation_counter._value
            },
            "tools": {
                "calls": self.tool_call_counter._value
            },
            "errors": {
                "total": self.error_counter._value
            },
            "budget": {
                "remaining": self.budget_remaining_gauge._value
            },
            "memory": {
                "usage_bytes": self.memory_usage_gauge._value
            }
        }
    
    async def get_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera eventi di telemetria con filtri opzionali
        
        Args:
            filters: Filtri da applicare
            limit: Numero massimo di eventi da restituire
            include_metadata: Se includere i metadata
            
        Returns:
            Lista di eventi formattati
        """
        try:
            # Use real database/storage for telemetry data
            from .telemetry_api import TelemetryAPIService
            
            # Usa il servizio stub per ora
            stub_service = TelemetryAPIService()
            return await stub_service.get_events(filters, limit, include_metadata)
            
        except Exception as e:
            logger.error(f"Error retrieving telemetry events: {str(e)}")
            return []
    
    async def get_status(self) -> Dict[str, Any]:
        """Restituisce lo stato del servizio di telemetria"""
        try:
            return {
                "status": "healthy",
                "total_events": await self._get_total_events_count(),
                "total_conversations": await self._get_total_conversations_count(),
                "total_agents": await self._get_total_agents_count(),
                "last_updated": datetime.utcnow().isoformat(),
                "sample_data": False,
                "backend": "convergio-telemetry",
                "version": "1.0.0"
            }
        except Exception as e:
            logger.error(f"Error getting telemetry status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_total_events_count(self) -> int:
        """Get total telemetry events count from storage."""
        try:
            # Try to get from Redis cache first
            from ...core.redis import get_redis_client
            redis_client = await get_redis_client()
            cached_count = await redis_client.get("telemetry:events:count")
            
            if cached_count:
                return int(cached_count)
            
            # Fallback to calculating from active spans and metrics
            active_events = len(self.active_spans)
            
            # Cache the result for 5 minutes
            await redis_client.setex("telemetry:events:count", 300, active_events)
            return active_events
            
        except Exception as e:
            logger.warning(f"Failed to get events count: {e}")
            return len(self.active_spans)
    
    async def _get_total_conversations_count(self) -> int:
        """Get total conversations count."""
        try:
            # Try to get from memory system or database
            from ..memory.autogen_memory_system import AutoGenMemorySystem
            memory_system = AutoGenMemorySystem()
            
            # Count unique conversation IDs from memory
            conversations = await memory_system.get_conversation_count()
            return conversations
            
        except Exception as e:
            logger.warning(f"Failed to get conversations count: {e}")
            return 0
    
    async def _get_total_agents_count(self) -> int:
        """Get total agents count from agent loader."""
        try:
            from ..agent_loader import DynamicAgentLoader
            loader = DynamicAgentLoader("src/agents/definitions")
            agents_metadata = loader.scan_and_load_agents()
            return len(agents_metadata)
            
        except Exception as e:
            logger.warning(f"Failed to get agents count: {e}")
            return 0
    
    def shutdown(self):
        """Shutdown telemetry system"""
        logger.info("Shutting down telemetry system")
        
        # Flush all spans
        for span in self.active_spans.values():
            if span.is_recording():
                span.end()
        
        # Shutdown providers
        self.tracer_provider.shutdown()
        self.meter_provider.shutdown()


# Global telemetry instance
_telemetry: Optional[ConvergioTelemetry] = None


def initialize_telemetry(service_name: str = "convergio-autogen", endpoint: Optional[str] = None):
    """Initialize global telemetry instance"""
    global _telemetry
    _telemetry = ConvergioTelemetry(service_name, endpoint)
    return _telemetry


def get_telemetry() -> Optional[ConvergioTelemetry]:
    """Get global telemetry instance"""
    return _telemetry


# Decorator for automatic tracing
def trace_method(name: Optional[str] = None):
    """Decorator to automatically trace methods"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            method_name = name or f"{func.__module__}.{func.__name__}"
            telemetry = get_telemetry()
            
            if not telemetry:
                return await func(*args, **kwargs)
            
            with telemetry.tracer.start_as_current_span(
                method_name,
                kind=trace.SpanKind.INTERNAL
            ) as span:
                try:
                    span.set_attribute("method.name", method_name)
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        def sync_wrapper(*args, **kwargs):
            method_name = name or f"{func.__module__}.{func.__name__}"
            telemetry = get_telemetry()
            
            if not telemetry:
                return func(*args, **kwargs)
            
            with telemetry.tracer.start_as_current_span(
                method_name,
                kind=trace.SpanKind.INTERNAL
            ) as span:
                try:
                    span.set_attribute("method.name", method_name)
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Export main components
__all__ = [
    "ConvergioTelemetry",
    "TelemetryContext",
    "ObservabilityEvent",
    "initialize_telemetry",
    "get_telemetry",
    "trace_method"
]