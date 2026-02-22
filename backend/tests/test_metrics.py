"""Tests for Prometheus metrics and Grafana dashboard artifacts."""

from pathlib import Path

from prometheus_client.metrics import Counter, Gauge, Histogram


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_metrics_module_exposes_expected_metric_instances():
    from core import metrics

    expected = {
        "requests_total": Counter,
        "agent_invocations_total": Counter,
        "errors_total": Counter,
        "response_time_seconds": Histogram,
        "agent_latency_seconds": Histogram,
        "active_users": Gauge,
        "active_agents": Gauge,
    }

    for attr_name, metric_type in expected.items():
        metric = getattr(metrics, attr_name)
        assert isinstance(metric, metric_type)


def test_metrics_have_expected_prometheus_names():
    from core import metrics

    # Prometheus Counter strips the "_total" suffix on the internal _name.
    assert metrics.requests_total._name == "convergio_requests"
    assert metrics.agent_invocations_total._name == "convergio_agent_invocations"
    assert metrics.errors_total._name == "convergio_errors"
    assert metrics.response_time_seconds._name == "convergio_response_time_seconds"
    assert metrics.agent_latency_seconds._name == "convergio_agent_latency_seconds"
    assert metrics.active_users._name == "convergio_active_users"
    assert metrics.active_agents._name == "convergio_active_agents"


def test_grafana_dashboard_exists_and_contains_key_panels():
    dashboard_path = PROJECT_ROOT / "grafana" / "dashboards" / "convergio-overview.json"
    assert dashboard_path.is_file()

    import json

    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    titles = {panel["title"] for panel in dashboard["panels"]}

    assert "Request Rate" in titles
    assert "Error Rate" in titles
    assert "Response Time (p95)" in titles
    assert "Agent Latency (p95)" in titles
    assert "Active Users" in titles
    assert "Active Agents" in titles
