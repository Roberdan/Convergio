//! Domain types for the delegation pipeline.

use serde::{Deserialize, Serialize};

/// Request body for `POST /api/delegate/spawn`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegateRequest {
    pub peer: String,
    pub plan_id: i64,
    pub tmux_session: Option<String>,
    pub tmux_window: Option<String>,
}

/// Request body for `POST /api/mesh/delegate`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegateMarkRequest {
    pub plan_id: i64,
    pub peer: String,
}

/// Persisted delegation record from the `delegations` table.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegationRecord {
    pub id: i64,
    pub delegation_id: String,
    pub plan_id: i64,
    pub peer_name: String,
    pub status: String,
    pub current_step: String,
    pub source_path: Option<String>,
    pub remote_path: Option<String>,
    pub error_message: Option<String>,
    pub started_at: String,
    pub completed_at: Option<String>,
}

/// Pipeline execution status.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum DelegationStatus {
    Pending,
    CopyingFiles,
    Spawning,
    Running,
    SyncingBack,
    Done,
    Failed(String),
}

impl std::fmt::Display for DelegationStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Pending => write!(f, "pending"),
            Self::CopyingFiles => write!(f, "copying_files"),
            Self::Spawning => write!(f, "spawning"),
            Self::Running => write!(f, "running"),
            Self::SyncingBack => write!(f, "syncing_back"),
            Self::Done => write!(f, "done"),
            Self::Failed(msg) => write!(f, "failed:{msg}"),
        }
    }
}

impl DelegationStatus {
    /// Parse from DB string representation.
    pub fn from_db(s: &str) -> Self {
        match s {
            "pending" => Self::Pending,
            "copying_files" => Self::CopyingFiles,
            "spawning" => Self::Spawning,
            "running" => Self::Running,
            "syncing_back" => Self::SyncingBack,
            "done" => Self::Done,
            other => {
                if let Some(msg) = other.strip_prefix("failed:") {
                    Self::Failed(msg.to_string())
                } else {
                    Self::Failed(format!("unknown status: {other}"))
                }
            }
        }
    }
}

/// Pipeline execution step for progress tracking.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum DelegationStep {
    Init,
    FileCopy,
    Spawn,
    Execute,
    SyncBack,
    Complete,
}

impl std::fmt::Display for DelegationStep {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Init => write!(f, "init"),
            Self::FileCopy => write!(f, "file_copy"),
            Self::Spawn => write!(f, "spawn"),
            Self::Execute => write!(f, "execute"),
            Self::SyncBack => write!(f, "sync_back"),
            Self::Complete => write!(f, "complete"),
        }
    }
}

/// Configuration for the delegation pipeline.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineConfig {
    pub project_root: String,
    pub remote_base: String,
    pub exclude_patterns: Vec<String>,
}

impl Default for PipelineConfig {
    fn default() -> Self {
        Self {
            project_root: ".".to_string(),
            remote_base: "/tmp/convergio-delegation".to_string(),
            exclude_patterns: vec![
                ".git".to_string(),
                "target".to_string(),
                "node_modules".to_string(),
                ".worktrees".to_string(),
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_display_roundtrip() {
        assert_eq!(DelegationStatus::Pending.to_string(), "pending");
        assert_eq!(DelegationStatus::CopyingFiles.to_string(), "copying_files");
        assert_eq!(DelegationStatus::Done.to_string(), "done");
        let f = DelegationStatus::Failed("timeout".into());
        assert_eq!(f.to_string(), "failed:timeout");
    }

    #[test]
    fn status_from_db() {
        assert_eq!(
            DelegationStatus::from_db("pending"),
            DelegationStatus::Pending
        );
        assert_eq!(DelegationStatus::from_db("done"), DelegationStatus::Done);
        assert_eq!(
            DelegationStatus::from_db("failed:ssh error"),
            DelegationStatus::Failed("ssh error".into())
        );
    }

    #[test]
    fn step_display() {
        assert_eq!(DelegationStep::Init.to_string(), "init");
        assert_eq!(DelegationStep::FileCopy.to_string(), "file_copy");
        assert_eq!(DelegationStep::Complete.to_string(), "complete");
    }

    #[test]
    fn pipeline_config_default_excludes() {
        let cfg = PipelineConfig::default();
        assert!(cfg.exclude_patterns.contains(&".git".to_string()));
        assert!(cfg.exclude_patterns.contains(&"target".to_string()));
        assert!(cfg.exclude_patterns.contains(&"node_modules".to_string()));
        assert!(cfg.exclude_patterns.contains(&".worktrees".to_string()));
    }

    #[test]
    fn delegate_request_json_roundtrip() {
        let req = DelegateRequest {
            peer: "studio-mac".into(),
            plan_id: 42,
            tmux_session: Some("convergio".into()),
            tmux_window: Some("task-1".into()),
        };
        let json = serde_json::to_string(&req).unwrap();
        let back: DelegateRequest = serde_json::from_str(&json).unwrap();
        assert_eq!(back.peer, "studio-mac");
        assert_eq!(back.plan_id, 42);
    }
}
