//! Data types for the scheduler policy engine.

use serde::{Deserialize, Serialize};

/// A request to schedule a task on the best available peer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulingRequest {
    pub task_id: i64,
    pub plan_id: i64,
    /// Required capabilities: "gpu", "voice", "compute", etc.
    pub required_capabilities: Vec<String>,
    /// Preferred locality: "local", "studio-mac", etc.
    pub preferred_locality: Option<String>,
    /// Privacy level: "public", "org", "private".
    pub privacy_level: String,
    /// Maximum cost budget in USD.
    pub max_cost_usd: Option<f64>,
    /// Tier hint: "t1", "t2", "t3", "t4".
    pub tier_hint: Option<String>,
}

/// The result of scheduling: which peer was chosen and why.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulingDecision {
    pub task_id: i64,
    pub assigned_peer: String,
    pub assigned_tier: String,
    pub estimated_cost: f64,
    pub reason: String,
    pub alternatives: Vec<PeerCandidate>,
}

/// A scored candidate peer for a scheduling request.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerCandidate {
    pub peer_name: String,
    pub score: f64,
    pub capabilities_match: f64,
    pub cost_score: f64,
    pub load_score: f64,
    pub locality_bonus: f64,
}

/// Configurable weights for the scoring formula.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerPolicy {
    pub id: i64,
    pub name: String,
    /// Weight for capability match (default 0.4).
    pub weight_capability: f64,
    /// Weight for cost score (default 0.2).
    pub weight_cost: f64,
    /// Weight for load score (default 0.2).
    pub weight_load: f64,
    /// Weight for locality bonus (default 0.2).
    pub weight_locality: f64,
    /// Whether to enforce privacy constraints.
    pub privacy_enforce: bool,
}
