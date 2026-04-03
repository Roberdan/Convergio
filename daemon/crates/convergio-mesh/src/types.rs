//! Shared mesh types: sync metadata, change records, stats, delegation.

use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Metadata tracking last successful sync point per peer per table.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyncMeta {
    pub peer: String,
    pub table_name: String,
    pub last_synced: String,
}

/// A single row change to be replicated between peers.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncChange {
    pub table_name: String,
    pub pk: i64,
    pub data: serde_json::Value,
}

/// Aggregate mesh stats for health/metrics reporting.
#[derive(Debug, Clone, Default)]
pub struct MeshStats {
    pub peers_online: u64,
    pub total_synced: u64,
    pub last_sync_latency_ms: Option<i64>,
}

/// Status of a delegation to a remote peer.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DelegateStatus {
    Success,
    Failed,
    TimedOut,
    Cancelled,
}

/// Result of a delegation attempt.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegateResult {
    pub status: DelegateStatus,
    pub output: String,
    pub tokens_used: u64,
    pub duration: Duration,
    pub peer_name: String,
    pub worktree_path: Option<String>,
}

/// Tables eligible for timestamp-based sync.
/// Each table must have `id INTEGER PRIMARY KEY` and `updated_at TEXT`.
pub const SYNC_TABLES: &[&str] = &["plans", "tasks", "waves", "knowledge_base", "notifications"];

/// Default sync interval in seconds.
pub const DEFAULT_INTERVAL_SECS: u64 = 30;

/// Sync ticks between peer probes (10 * 30s = 5 min).
pub const PROBE_EVERY_N_TICKS: u64 = 10;

/// Peer heartbeat timeout in seconds (10 min).
pub const HEARTBEAT_TIMEOUT_SECS: i64 = 600;

/// Schema version response from a peer's /api/health endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerSchemaInfo {
    pub peer_name: String,
    pub schema_versions: Vec<(String, u32)>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sync_change_serialization() {
        let change = SyncChange {
            table_name: "plans".into(),
            pk: 42,
            data: serde_json::json!({"status": "doing"}),
        };
        let json = serde_json::to_string(&change).unwrap();
        let back: SyncChange = serde_json::from_str(&json).unwrap();
        assert_eq!(back.pk, 42);
    }

    #[test]
    fn delegate_status_serialization() {
        let s = DelegateStatus::Success;
        let json = serde_json::to_string(&s).unwrap();
        assert!(json.contains("Success"));
    }
}
