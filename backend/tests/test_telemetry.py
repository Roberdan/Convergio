"""Tests for core OpenTelemetry integration."""

from fastapi import FastAPI


def test_create_tracer_provider_sets_resource_attributes(monkeypatch):
    from core.telemetry import create_tracer_provider

    monkeypatch.setenv("OTEL_SERVICE_NAME", "convergio-backend")
    monkeypatch.setenv("ENVIRONMENT", "staging")

    provider = create_tracer_provider()
    attrs = provider.resource.attributes

    assert attrs["service.name"] == "convergio-backend"
    assert attrs["deployment.environment"] == "staging"


def test_instrument_fastapi_app_calls_instrumentor(monkeypatch):
    import core.telemetry as telemetry

    captured = {}

    class DummyInstrumentor:
        def instrument_app(self, app, **kwargs):
            captured["app"] = app
            captured["kwargs"] = kwargs

    monkeypatch.setattr(telemetry, "FastAPIInstrumentor", DummyInstrumentor)

    app = FastAPI()
    telemetry.instrument_fastapi_app(app)

    assert captured["app"] is app
    assert "excluded_urls" in captured["kwargs"]


def test_agent_operation_span_records_agent_attributes():
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from core.telemetry import agent_operation_span

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("test")
    with agent_operation_span(
        tracer,
        agent_name="planner",
        operation="route",
        attributes={"task_id": "T6-02"},
    ):
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "agent.planner.route"
    assert span.attributes["agent.name"] == "planner"
    assert span.attributes["agent.operation"] == "route"
    assert span.attributes["task_id"] == "T6-02"


def test_build_otlp_exporter_kwargs_uses_grafana_endpoint(monkeypatch):
    from core.telemetry import build_otlp_exporter_kwargs

    monkeypatch.setenv("GRAFANA_CLOUD_OTLP_ENDPOINT", "https://grafana.example/otlp")
    monkeypatch.setenv("GRAFANA_CLOUD_OTLP_API_KEY", "secret-token")

    kwargs = build_otlp_exporter_kwargs()

    assert kwargs["endpoint"] == "https://grafana.example/otlp"
    assert kwargs["headers"]["Authorization"].startswith("Bearer ")
