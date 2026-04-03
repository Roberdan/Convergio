//! Core kernel types — severity, status, actions, configuration.

use serde::{Deserialize, Serialize};

/// Classification severity for kernel health assessment.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum KernelSeverity {
    Ok,
    Warn,
    Critical,
}

impl std::fmt::Display for KernelSeverity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Ok => write!(f, "ok"),
            Self::Warn => write!(f, "warn"),
            Self::Critical => write!(f, "critical"),
        }
    }
}

/// Action recommended by the kernel after classification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KernelAction {
    pub severity: KernelSeverity,
    pub action: String,
    pub reason: String,
}

/// Current kernel status snapshot.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KernelStatus {
    pub models_loaded: bool,
    pub ram_gb: f64,
    pub uptime_secs: u64,
    pub active_node: Option<String>,
    pub last_check: Option<String>,
}

/// Kernel configuration stored in kernel_config table.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KernelConfig {
    pub active_node: Option<String>,
    pub default_model: String,
}

impl Default for KernelConfig {
    fn default() -> Self {
        Self {
            active_node: None,
            default_model: "qwen2.5-7b-instruct-4bit".to_string(),
        }
    }
}

/// Inference routing level.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InferenceLevel {
    /// Local model (Qwen via MLX on Apple Silicon).
    Local,
    /// Cloud model (Claude Opus via API).
    Cloud,
}

/// Voice intent classification results.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum VoiceIntent {
    StatusCheck,
    CostQuery,
    PlanQuery,
    Restart,
    Mute,
    EscalateToAli,
    CreateProject,
    AskOrg,
    CreateOrgFrom,
    Unknown,
}

/// Evidence check result for task verification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceCheck {
    pub name: String,
    pub passed: bool,
    pub detail: String,
}

/// Evidence report for a task status transition.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceReport {
    pub task_id: i64,
    pub status_requested: String,
    pub checks: Vec<EvidenceCheck>,
    pub passed: bool,
    pub severity: KernelSeverity,
    pub action: String,
    pub reason: String,
}

/// Result of a health monitor check cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KernelCheckResult {
    pub check_name: String,
    pub ok: bool,
    pub details: String,
}
