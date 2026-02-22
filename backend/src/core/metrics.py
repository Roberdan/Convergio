"""Prometheus metrics definitions for Convergio backend."""

from prometheus_client import Counter, Gauge, Histogram

REQUEST_LABELS = ("method", "route", "status_code")
AGENT_LABELS = ("agent_name", "operation", "status")
ERROR_LABELS = ("component", "error_type")

requests_total = Counter(
    "convergio_requests_total",
    "Total number of HTTP requests processed by the backend.",
    REQUEST_LABELS,
)

agent_invocations_total = Counter(
    "convergio_agent_invocations_total",
    "Total number of AI agent invocations.",
    AGENT_LABELS,
)

errors_total = Counter(
    "convergio_errors_total",
    "Total number of backend errors by component and type.",
    ERROR_LABELS,
)

response_time_seconds = Histogram(
    "convergio_response_time_seconds",
    "Response time for backend HTTP requests.",
    REQUEST_LABELS,
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

agent_latency_seconds = Histogram(
    "convergio_agent_latency_seconds",
    "Execution latency for AI agent operations.",
    AGENT_LABELS,
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

active_users = Gauge(
    "convergio_active_users",
    "Current number of active users.",
)

active_agents = Gauge(
    "convergio_active_agents",
    "Current number of active agents.",
)
