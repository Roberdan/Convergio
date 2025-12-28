"""
OpenTelemetry Integration for Convergio
Comprehensive observability with spans export and metrics collection
"""

import os
import json
from typing import Dict, Any, Optional
from contextlib import contextmanager
import structlog

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.propagate import set_global_textmap

# Optional instrumentation - these may not be installed
try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    REQUESTS_INSTRUMENTATION_AVAILABLE = True
except ImportError:
    REQUESTS_INSTRUMENTATION_AVAILABLE = False

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FASTAPI_INSTRUMENTATION_AVAILABLE = True
except ImportError:
    FASTAPI_INSTRUMENTATION_AVAILABLE = False

try:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    REDIS_INSTRUMENTATION_AVAILABLE = True
except ImportError:
    REDIS_INSTRUMENTATION_AVAILABLE = False

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    PrometheusMetricReader = None

from ..utils.config import get_settings

logger = structlog.get_logger()


class OTELManager:
    """Manages OpenTelemetry configuration and instrumentation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tracer = None
        self.meter = None
        self.initialized = False
        
        # Metrics collectors
        self.conversation_counter = None
        self.turn_histogram = None
        self.token_counter = None
        self.cost_histogram = None
        self.latency_histogram = None
        self.error_counter = None
        self.agent_invocation_counter = None
        self.rag_hit_counter = None
        self.selection_time_histogram = None
        
    def initialize(
        self,
        service_name: str = "convergio-agents",
        otlp_endpoint: Optional[str] = None,
        enable_console_export: bool = False,
        enable_prometheus: bool = True
    ):
        """Initialize OpenTelemetry with OTLP exporter"""
        
        if self.initialized:
            logger.warning("OTEL already initialized")
            return
        
        logger.info("🔭 Initializing OpenTelemetry", 
                   service_name=service_name,
                   endpoint=otlp_endpoint)
        
        # Configure resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", "local")
        })
        
        # Setup tracing
        self._setup_tracing(resource, otlp_endpoint, enable_console_export)
        
        # Setup metrics
        self._setup_metrics(resource, otlp_endpoint, enable_prometheus)
        
        # Setup propagator for distributed tracing
        set_global_textmap(TraceContextTextMapPropagator())
        
        # Auto-instrument libraries
        self._auto_instrument()
        
        # Initialize metric collectors
        self._initialize_metrics()
        
        self.initialized = True
        logger.info("✅ OpenTelemetry initialized successfully")
    
    def _setup_tracing(
        self,
        resource: Resource,
        otlp_endpoint: Optional[str],
        enable_console: bool
    ):
        """Setup tracing with OTLP exporter"""
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter if endpoint provided
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True  # Use insecure for local development
            )
            provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            logger.info(f"📡 OTLP trace exporter configured: {otlp_endpoint}")
        
        # Add console exporter for debugging
        if enable_console:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            logger.info("📺 Console trace exporter enabled")
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)
    
    def _setup_metrics(
        self,
        resource: Resource,
        otlp_endpoint: Optional[str],
        enable_prometheus: bool
    ):
        """Setup metrics with OTLP and Prometheus exporters"""
        
        readers = []
        
        # Add OTLP metric exporter
        if otlp_endpoint:
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            readers.append(otlp_metric_exporter)
            logger.info(f"📊 OTLP metric exporter configured: {otlp_endpoint}")
        
        # Add Prometheus exporter
        if enable_prometheus and PROMETHEUS_AVAILABLE:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)
            logger.info("📈 Prometheus metric exporter enabled on :9090/metrics")
        elif enable_prometheus:
            logger.warning("⚠️ Prometheus requested but not available - install opentelemetry-exporter-prometheus")
        
        # Create meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )
        
        # Set global meter provider
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter(__name__)
    
    def _auto_instrument(self):
        """Auto-instrument common libraries"""
        
        try:
            # Instrument HTTP requests
            if REQUESTS_INSTRUMENTATION_AVAILABLE:
                RequestsInstrumentor().instrument()
            logger.info("🔧 Instrumented requests library")
        except Exception as e:
            logger.warning(f"Failed to instrument requests: {e}")
        
        try:
            # Instrument Redis
            if REDIS_INSTRUMENTATION_AVAILABLE:
                RedisInstrumentor().instrument()
            logger.info("🔧 Instrumented Redis client")
        except Exception as e:
            logger.warning(f"Failed to instrument Redis: {e}")
    
    def _initialize_metrics(self):
        """Initialize metric collectors"""
        
        if not self.meter:
            return
        
        # Conversation metrics
        self.conversation_counter = self.meter.create_counter(
            name="convergio_conversations_total",
            description="Total number of conversations",
            unit="1"
        )
        
        self.turn_histogram = self.meter.create_histogram(
            name="convergio_conversation_turns",
            description="Number of turns per conversation",
            unit="1"
        )
        
        # Token and cost metrics
        self.token_counter = self.meter.create_counter(
            name="convergio_tokens_total",
            description="Total tokens consumed",
            unit="1"
        )
        
        self.cost_histogram = self.meter.create_histogram(
            name="convergio_cost_usd",
            description="Cost per conversation in USD",
            unit="USD"
        )
        
        # Performance metrics
        self.latency_histogram = self.meter.create_histogram(
            name="convergio_latency_ms",
            description="Operation latency in milliseconds",
            unit="ms"
        )
        
        self.error_counter = self.meter.create_counter(
            name="convergio_errors_total",
            description="Total number of errors",
            unit="1"
        )
        
        # Agent metrics
        self.agent_invocation_counter = self.meter.create_counter(
            name="convergio_agent_invocations_total",
            description="Total agent invocations",
            unit="1"
        )
        
        # RAG metrics
        self.rag_hit_counter = self.meter.create_counter(
            name="convergio_rag_hits_total",
            description="RAG context retrievals",
            unit="1"
        )
        
        # Selection metrics
        self.selection_time_histogram = self.meter.create_histogram(
            name="convergio_speaker_selection_time_ms",
            description="Speaker selection time",
            unit="ms"
        )
        
        logger.info("📊 Metrics collectors initialized")
    
    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL
    ):
        """Create a traced span context manager"""
        
        if not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes or {}
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def record_conversation_start(
        self,
        conversation_id: str,
        user_id: str,
        agent_name: Optional[str] = None
    ):
        """Record conversation start"""
        
        if self.conversation_counter:
            self.conversation_counter.add(
                1,
                attributes={
                    "user_id": user_id,
                    "agent": agent_name or "group_chat"
                }
            )
        
        with self.span(
            "conversation.start",
            attributes={
                "conversation_id": conversation_id,
                "user_id": user_id,
                "agent": agent_name
            }
        ) as span:
            if span:
                span.add_event("conversation_started")
    
    def record_turn(
        self,
        conversation_id: str,
        turn_number: int,
        agent_name: str,
        tokens: int,
        duration_ms: int
    ):
        """Record a conversation turn"""
        
        attributes = {
            "conversation_id": conversation_id,
            "turn": turn_number,
            "agent": agent_name
        }
        
        if self.token_counter:
            self.token_counter.add(tokens, attributes=attributes)
        
        if self.latency_histogram:
            self.latency_histogram.record(duration_ms, attributes=attributes)
        
        if self.agent_invocation_counter:
            self.agent_invocation_counter.add(1, attributes={"agent": agent_name})
        
        with self.span(
            f"turn.{turn_number}",
            attributes={
                **attributes,
                "tokens": tokens,
                "duration_ms": duration_ms
            }
        ) as span:
            if span:
                span.add_event(f"turn_completed_by_{agent_name}")
    
    def record_conversation_end(
        self,
        conversation_id: str,
        total_turns: int,
        total_tokens: int,
        total_cost_usd: float,
        duration_seconds: float
    ):
        """Record conversation end"""
        
        if self.turn_histogram:
            self.turn_histogram.record(
                total_turns,
                attributes={"conversation_id": conversation_id}
            )
        
        if self.cost_histogram:
            self.cost_histogram.record(
                total_cost_usd,
                attributes={"conversation_id": conversation_id}
            )
        
        with self.span(
            "conversation.end",
            attributes={
                "conversation_id": conversation_id,
                "total_turns": total_turns,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost_usd,
                "duration_seconds": duration_seconds
            }
        ) as span:
            if span:
                span.add_event("conversation_completed")
    
    def record_rag_retrieval(
        self,
        user_id: str,
        query: str,
        facts_retrieved: int,
        duration_ms: int
    ):
        """Record RAG retrieval"""
        
        if self.rag_hit_counter:
            self.rag_hit_counter.add(
                1,
                attributes={
                    "user_id": user_id,
                    "facts_count": facts_retrieved
                }
            )
        
        with self.span(
            "rag.retrieval",
            attributes={
                "user_id": user_id,
                "query_length": len(query),
                "facts_retrieved": facts_retrieved,
                "duration_ms": duration_ms
            }
        ) as span:
            if span:
                span.add_event("rag_context_retrieved")
    
    def record_speaker_selection(
        self,
        turn: int,
        selected_agent: str,
        selection_time_ms: int,
        score: float
    ):
        """Record speaker selection"""
        
        if self.selection_time_histogram:
            self.selection_time_histogram.record(
                selection_time_ms,
                attributes={
                    "turn": turn,
                    "selected_agent": selected_agent
                }
            )
        
        with self.span(
            "speaker.selection",
            attributes={
                "turn": turn,
                "selected_agent": selected_agent,
                "score": score,
                "selection_time_ms": selection_time_ms
            }
        ) as span:
            if span:
                span.add_event(f"selected_{selected_agent}")
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Record an error"""
        
        if self.error_counter:
            self.error_counter.add(
                1,
                attributes={
                    "error_type": error_type,
                    **({} if not context else context)
                }
            )
        
        with self.span(
            "error",
            attributes={
                "error_type": error_type,
                "error_message": error_message,
                **(context or {})
            }
        ) as span:
            if span:
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.add_event("error_occurred")
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context for propagation"""
        
        if not self.tracer:
            return {}
        
        propagator = TraceContextTextMapPropagator()
        carrier = {}
        propagator.inject(carrier)
        return carrier
    
    def create_child_span(
        self,
        name: str,
        parent_context: Dict[str, str],
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Create a child span from parent context"""
        
        if not self.tracer:
            return None
        
        propagator = TraceContextTextMapPropagator()
        context = propagator.extract(parent_context)
        
        return self.tracer.start_span(
            name,
            context=context,
            attributes=attributes or {}
        )


class OTELDashboard:
    """Dashboard configuration for OTEL metrics"""
    
    @staticmethod
    def generate_grafana_dashboard() -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        
        return {
            "dashboard": {
                "title": "Convergio AutoGen Observability",
                "panels": [
                    {
                        "title": "Conversations per Hour",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(convergio_conversations_total[1h])"
                        }]
                    },
                    {
                        "title": "Average Turns per Conversation",
                        "type": "stat",
                        "targets": [{
                            "expr": "avg(convergio_conversation_turns)"
                        }]
                    },
                    {
                        "title": "Token Usage Rate",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(convergio_tokens_total[5m])"
                        }]
                    },
                    {
                        "title": "Cost per Hour (USD)",
                        "type": "graph",
                        "targets": [{
                            "expr": "sum(rate(convergio_cost_usd[1h]))"
                        }]
                    },
                    {
                        "title": "P95 Latency (ms)",
                        "type": "graph",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, convergio_latency_ms)"
                        }]
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(convergio_errors_total[5m])"
                        }]
                    },
                    {
                        "title": "Agent Invocations",
                        "type": "graph",
                        "targets": [{
                            "expr": "sum by (agent) (rate(convergio_agent_invocations_total[5m]))"
                        }]
                    },
                    {
                        "title": "RAG Hit Rate",
                        "type": "graph",
                        "targets": [{
                            "expr": "rate(convergio_rag_hits_total[5m])"
                        }]
                    },
                    {
                        "title": "Speaker Selection Time P95",
                        "type": "stat",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, convergio_speaker_selection_time_ms)"
                        }]
                    }
                ],
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "refresh": "10s"
            }
        }
    
    @staticmethod
    def export_dashboard_json(output_path: str):
        """Export dashboard configuration to file"""
        
        dashboard = OTELDashboard.generate_grafana_dashboard()
        
        with open(output_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        logger.info(f"📊 Dashboard exported to {output_path}")


# Global OTEL manager instance
_otel_manager: Optional[OTELManager] = None


def initialize_otel(
    service_name: str = "convergio-agents",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = False,
    enable_prometheus: bool = True
) -> OTELManager:
    """Initialize global OTEL manager"""
    
    global _otel_manager
    
    if not otlp_endpoint:
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    
    _otel_manager = OTELManager()
    _otel_manager.initialize(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        enable_console_export=enable_console,
        enable_prometheus=enable_prometheus
    )
    
    return _otel_manager


def get_otel_manager() -> Optional[OTELManager]:
    """Get global OTEL manager"""
    return _otel_manager


def instrument_fastapi(app):
    """Instrument FastAPI application"""
    
    if FASTAPI_INSTRUMENTATION_AVAILABLE:
        FastAPIInstrumentor.instrument_app(app)
    else:
        logger.warning("FastAPI instrumentation not available")
    logger.info("🔧 Instrumented FastAPI application")
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        # Prometheus exporter handles this automatically
        return {"message": "Metrics available at :9090/metrics"}
    
    # Add health check with trace
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        manager = get_otel_manager()
        if manager:
            with manager.span("health_check"):
                return {"status": "healthy", "otel": "enabled"}
        return {"status": "healthy", "otel": "disabled"}


__all__ = [
    "OTELManager",
    "OTELDashboard",
    "initialize_otel",
    "get_otel_manager",
    "instrument_fastapi"
]