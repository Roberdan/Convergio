//! Core types for the observability aggregation layer.

use serde::{Deserialize, Serialize};

/// A unified timeline event aggregated from multiple sources.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimelineEvent {
    pub id: i64,
    pub source: EventSource,
    pub event_type: String,
    pub actor: String,
    pub org_id: Option<String>,
    pub node_id: Option<String>,
    pub summary: String,
    pub details_json: Option<String>,
    pub created_at: String,
}

/// Where a timeline event originated.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum EventSource {
    Orchestrator,
    Agent,
    Mesh,
    Billing,
    Security,
    System,
}

impl std::fmt::Display for EventSource {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Orchestrator => write!(f, "orchestrator"),
            Self::Agent => write!(f, "agent"),
            Self::Mesh => write!(f, "mesh"),
            Self::Billing => write!(f, "billing"),
            Self::Security => write!(f, "security"),
            Self::System => write!(f, "system"),
        }
    }
}

impl EventSource {
    pub fn from_str_value(s: &str) -> Self {
        match s {
            "orchestrator" => Self::Orchestrator,
            "agent" => Self::Agent,
            "mesh" => Self::Mesh,
            "billing" => Self::Billing,
            "security" => Self::Security,
            _ => Self::System,
        }
    }
}

/// Dashboard aggregate for cost-per-hour by org.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostPerHour {
    pub org_id: String,
    pub hour: String,
    pub cost_usd: f64,
}

/// Dashboard aggregate for task throughput per day.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskThroughput {
    pub org_id: String,
    pub date: String,
    pub tasks_completed: i64,
    pub tasks_failed: i64,
}

/// Dashboard aggregate for average model latency.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelLatency {
    pub model: String,
    pub avg_latency_ms: f64,
    pub p95_latency_ms: f64,
    pub request_count: i64,
}

/// An anomaly detected by the observatory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Anomaly {
    pub id: i64,
    pub kind: AnomalyKind,
    pub severity: Severity,
    pub entity_id: String,
    pub description: String,
    pub detected_at: String,
    pub resolved: bool,
}

/// Types of detectable anomalies.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AnomalyKind {
    CostSpike,
    ThroughputDrop,
    IdleAgent,
    HighErrorRate,
}

impl std::fmt::Display for AnomalyKind {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::CostSpike => write!(f, "cost_spike"),
            Self::ThroughputDrop => write!(f, "throughput_drop"),
            Self::IdleAgent => write!(f, "idle_agent"),
            Self::HighErrorRate => write!(f, "high_error_rate"),
        }
    }
}

impl AnomalyKind {
    pub fn from_str_value(s: &str) -> Self {
        match s {
            "cost_spike" => Self::CostSpike,
            "throughput_drop" => Self::ThroughputDrop,
            "idle_agent" => Self::IdleAgent,
            "high_error_rate" => Self::HighErrorRate,
            _ => Self::HighErrorRate,
        }
    }
}

/// Severity levels for anomalies.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Low => write!(f, "low"),
            Self::Medium => write!(f, "medium"),
            Self::High => write!(f, "high"),
            Self::Critical => write!(f, "critical"),
        }
    }
}

impl Severity {
    pub fn from_str_value(s: &str) -> Self {
        match s {
            "low" => Self::Low,
            "medium" => Self::Medium,
            "high" => Self::High,
            "critical" => Self::Critical,
            _ => Self::Medium,
        }
    }
}

/// Prometheus-compatible metric export entry.
#[derive(Debug, Clone, Serialize)]
pub struct PrometheusMetric {
    pub name: String,
    pub help: String,
    pub metric_type: String,
    pub value: f64,
    pub labels: Vec<(String, String)>,
}

/// Webhook export payload.
#[derive(Debug, Clone, Serialize)]
pub struct WebhookPayload {
    pub event_type: String,
    pub timestamp: String,
    pub data: serde_json::Value,
}

/// Full-text search result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub id: i64,
    pub source: String,
    pub snippet: String,
    pub score: f64,
    pub created_at: String,
}
