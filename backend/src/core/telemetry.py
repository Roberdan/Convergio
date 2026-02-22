"""Core OpenTelemetry setup for backend tracing and FastAPI instrumentation."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

_DEFAULT_EXCLUDED_URLS = "/health,/metrics"


def build_otlp_exporter_kwargs() -> dict[str, Any]:
    """Build OTLP exporter configuration, supporting Grafana Cloud defaults."""
    endpoint = (
        os.getenv("GRAFANA_CLOUD_OTLP_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or ""
    ).strip()

    headers: dict[str, str] = {}
    grafana_api_key = os.getenv("GRAFANA_CLOUD_OTLP_API_KEY", "").strip()
    if grafana_api_key:
        headers["Authorization"] = f"Bearer {grafana_api_key}"

    explicit_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip()
    if explicit_headers:
        for item in explicit_headers.split(","):
            key, _, value = item.partition("=")
            if key.strip() and value.strip():
                headers[key.strip()] = value.strip()

    kwargs: dict[str, Any] = {"endpoint": endpoint}
    if headers:
        kwargs["headers"] = headers
    return kwargs


def create_tracer_provider() -> TracerProvider:
    """Create TracerProvider with service resource and OTLP exporter when configured."""
    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "convergio-backend"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )
    provider = TracerProvider(resource=resource)

    exporter_kwargs = build_otlp_exporter_kwargs()
    if exporter_kwargs.get("endpoint"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs)))

    return provider


def instrument_fastapi_app(app: FastAPI, excluded_urls: str = _DEFAULT_EXCLUDED_URLS) -> None:
    """Enable automatic FastAPI tracing instrumentation."""
    FastAPIInstrumentor().instrument_app(app, excluded_urls=excluded_urls)


def initialize_telemetry(app: FastAPI | None = None) -> Tracer:
    """Initialize global tracer provider and optionally instrument FastAPI app."""
    provider = create_tracer_provider()
    trace.set_tracer_provider(provider)

    if app is not None:
        instrument_fastapi_app(app)

    return trace.get_tracer("core.telemetry")


@contextmanager
def agent_operation_span(
    tracer: Tracer,
    agent_name: str,
    operation: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Create a custom span for agent operations with consistent attributes."""
    span_name = f"agent.{agent_name}.{operation}"
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("agent.operation", operation)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span
