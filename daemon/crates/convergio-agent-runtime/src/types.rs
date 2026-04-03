//! Core types for the agent runtime.
//!
//! Models the agent lifecycle: allocation, ownership, workspace isolation,
//! scheduling priority, delegation borrowing, and liveness tracking.

use serde::{Deserialize, Serialize};

/// Errors specific to the agent runtime.
#[derive(Debug, thiserror::Error)]
pub enum RuntimeError {
    #[error("database: {0}")]
    Db(#[from] rusqlite::Error),
    #[error("pool: {0}")]
    Pool(#[from] r2d2::Error),
    #[error("json: {0}")]
    Json(#[from] serde_json::Error),
    #[error("budget exhausted for org {org_id}: spent {spent:.4} of {limit:.4}")]
    BudgetExhausted {
        org_id: String,
        spent: f64,
        limit: f64,
    },
    #[error("agent not found: {0}")]
    NotFound(String),
    #[error("scope violation: agent {agent_id} cannot access {resource}")]
    ScopeViolation { agent_id: String, resource: String },
    #[error("deadlock detected: circular delegation chain {chain}")]
    DeadlockDetected { chain: String },
    #[error("queue full for org {org_id}: depth {depth} >= max {max}")]
    BackpressureExceeded {
        org_id: String,
        depth: usize,
        max: usize,
    },
    #[error("{0}")]
    Internal(String),
}

pub type RuntimeResult<T> = Result<T, RuntimeError>;

/// Agent lifecycle stage.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AgentStage {
    Spawning,
    Running,
    Borrowed,
    Draining,
    Stopped,
    Reaped,
}

impl AgentStage {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Spawning => "spawning",
            Self::Running => "running",
            Self::Borrowed => "borrowed",
            Self::Draining => "draining",
            Self::Stopped => "stopped",
            Self::Reaped => "reaped",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "spawning" => Some(Self::Spawning),
            "running" => Some(Self::Running),
            "borrowed" => Some(Self::Borrowed),
            "draining" => Some(Self::Draining),
            "stopped" => Some(Self::Stopped),
            "reaped" => Some(Self::Reaped),
            _ => None,
        }
    }

    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Stopped | Self::Reaped)
    }

    pub fn is_active(&self) -> bool {
        matches!(self, Self::Running | Self::Borrowed)
    }
}

impl std::fmt::Display for AgentStage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Request to spawn a new agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpawnRequest {
    pub agent_name: String,
    pub org_id: String,
    pub task_id: Option<i64>,
    pub capabilities: Vec<String>,
    pub model_preference: Option<String>,
    pub budget_usd: f64,
    pub priority: i32,
}

/// A running agent instance in the runtime.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInstance {
    pub id: String,
    pub agent_name: String,
    pub org_id: String,
    pub task_id: Option<i64>,
    pub stage: AgentStage,
    pub workspace_path: Option<String>,
    pub model: Option<String>,
    pub node: String,
    pub budget_usd: f64,
    pub spent_usd: f64,
    pub priority: i32,
    pub created_at: String,
    pub last_heartbeat: Option<String>,
}

/// Delegation: borrowing an agent to another task/org.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Delegation {
    pub id: String,
    pub agent_id: String,
    pub from_org: String,
    pub to_org: String,
    pub to_task_id: Option<i64>,
    pub budget_usd: f64,
    pub timeout_secs: u64,
    pub created_at: String,
    pub expires_at: String,
    pub returned: bool,
}

/// Scheduling priority entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueEntry {
    pub request_id: String,
    pub org_id: String,
    pub priority: i32,
    pub created_at: String,
}

/// Live runtime view returned by GET /api/agents/runtime.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeView {
    pub active_agents: Vec<AgentInstance>,
    pub queue_depth: usize,
    pub total_budget_usd: f64,
    pub total_spent_usd: f64,
    pub delegations_active: usize,
    pub stale_count: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn agent_stage_roundtrip() {
        for stage in [
            AgentStage::Spawning,
            AgentStage::Running,
            AgentStage::Borrowed,
            AgentStage::Draining,
            AgentStage::Stopped,
            AgentStage::Reaped,
        ] {
            let s = stage.as_str();
            let parsed = AgentStage::parse(s).unwrap();
            assert_eq!(parsed, stage);
            assert_eq!(stage.to_string(), s);
        }
    }

    #[test]
    fn agent_stage_parse_invalid() {
        assert!(AgentStage::parse("bogus").is_none());
    }

    #[test]
    fn terminal_and_active_stages() {
        assert!(!AgentStage::Running.is_terminal());
        assert!(AgentStage::Running.is_active());
        assert!(AgentStage::Stopped.is_terminal());
        assert!(!AgentStage::Stopped.is_active());
        assert!(AgentStage::Reaped.is_terminal());
    }

    #[test]
    fn runtime_view_serializes() {
        let view = RuntimeView {
            active_agents: vec![],
            queue_depth: 5,
            total_budget_usd: 100.0,
            total_spent_usd: 42.5,
            delegations_active: 2,
            stale_count: 0,
        };
        let json = serde_json::to_string(&view).unwrap();
        assert!(json.contains("42.5"));
        assert!(json.contains("queue_depth"));
    }
}
