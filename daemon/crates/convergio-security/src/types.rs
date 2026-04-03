//! Security types — errors, ACL, audit, budget.

use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error)]
pub enum SecurityError {
    #[error("access denied: {0}")]
    AccessDenied(String),
    #[error("sandbox violation: {0}")]
    SandboxViolation(String),
    #[error("budget exceeded: {0}")]
    BudgetExceeded(String),
    #[error("audit error: {0}")]
    AuditError(String),
}

/// ACL rule for a specific resource type.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AclRule {
    pub resource_type: ResourceType,
    pub pattern: String,
    pub permissions: Vec<Permission>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ResourceType {
    Filesystem,
    Network,
    Api,
    Database,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Permission {
    Read,
    Write,
    Execute,
    Delete,
}

/// Cryptographic audit chain entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    pub id: u64,
    pub agent_id: String,
    pub action: String,
    pub target: String,
    pub timestamp: String,
    pub params_hash: String,
    pub prev_hash: String,
    pub entry_hash: String,
}

/// Per-agent budget configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentBudget {
    pub agent_id: String,
    pub max_api_calls_per_hour: u64,
    pub max_tokens_per_day: u64,
    pub max_compute_seconds: u64,
    pub max_storage_bytes: u64,
}

impl Default for AgentBudget {
    fn default() -> Self {
        Self {
            agent_id: String::new(),
            max_api_calls_per_hour: 1000,
            max_tokens_per_day: 10_000_000,
            max_compute_seconds: 3600,
            max_storage_bytes: 1_073_741_824,
        }
    }
}
