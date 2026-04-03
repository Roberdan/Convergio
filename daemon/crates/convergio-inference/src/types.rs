//! Inference types — tiers, requests, responses, routing decisions.

use serde::{Deserialize, Serialize};

/// Model tier classification — maps to capability requirements.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum InferenceTier {
    T1Trivial,
    T2Standard,
    T3Complex,
    T4Critical,
}

impl InferenceTier {
    /// Short label for serialization and DB storage.
    pub fn label(&self) -> &'static str {
        match self {
            Self::T1Trivial => "t1",
            Self::T2Standard => "t2",
            Self::T3Complex => "t3",
            Self::T4Critical => "t4",
        }
    }

    /// Parse from short label.
    pub fn from_label(s: &str) -> Option<Self> {
        match s {
            "t1" => Some(Self::T1Trivial),
            "t2" => Some(Self::T2Standard),
            "t3" => Some(Self::T3Complex),
            "t4" => Some(Self::T4Critical),
            _ => None,
        }
    }
}

/// Routing constraints from the caller.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceConstraints {
    pub max_latency_ms: Option<u64>,
    pub max_cost: Option<f64>,
}

/// Incoming inference request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceRequest {
    pub prompt: String,
    pub max_tokens: u32,
    /// Caller hint — router may override based on health/budget.
    pub tier_hint: Option<InferenceTier>,
    pub agent_id: String,
    pub org_id: Option<String>,
    pub plan_id: Option<i64>,
    pub constraints: InferenceConstraints,
}

/// Result returned after routing and inference.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceResponse {
    pub content: String,
    pub model_used: String,
    pub latency_ms: u64,
    pub tokens_used: u32,
    pub cost: f64,
}

/// Provider classification.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ModelProvider {
    Local,
    Cloud,
}

/// A registered model endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelEndpoint {
    pub name: String,
    pub provider: ModelProvider,
    pub url: String,
    /// Cost per 1K input tokens (USD).
    pub cost_per_1k_input: f64,
    /// Cost per 1K output tokens (USD).
    pub cost_per_1k_output: f64,
    /// Inclusive tier range this model serves.
    pub tier_range: (InferenceTier, InferenceTier),
    pub healthy: bool,
}

/// The router's routing decision (for logging, API, and fallback chains).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingDecision {
    pub selected_model: String,
    pub reason: String,
    pub effective_tier: String,
    pub fallback_chain: Vec<String>,
    pub budget_remaining: Option<f64>,
}

/// Cost record for tracking spend per agent/org/plan.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostRecord {
    pub agent_id: String,
    pub org_id: Option<String>,
    pub plan_id: Option<i64>,
    pub model: String,
    pub tokens_input: u32,
    pub tokens_output: u32,
    pub cost_usd: f64,
    pub timestamp: String,
}

/// Aggregated costs for a given scope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostSummary {
    pub scope: String,
    pub scope_id: String,
    pub total_tokens: u64,
    pub total_cost_usd: f64,
    pub request_count: u64,
    pub models_used: Vec<String>,
}
