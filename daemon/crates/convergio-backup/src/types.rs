//! Core types for the backup module.

use serde::{Deserialize, Serialize};

/// Errors produced by the backup module.
#[derive(Debug, thiserror::Error)]
pub enum BackupError {
    #[error("database error: {0}")]
    Db(#[from] rusqlite::Error),

    #[error("pool error: {0}")]
    Pool(#[from] r2d2::Error),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("snapshot not found: {0}")]
    SnapshotNotFound(String),

    #[error("invalid config: {0}")]
    InvalidConfig(String),

    #[error("restore failed: {0}")]
    RestoreFailed(String),
}

pub type BackupResult<T> = Result<T, BackupError>;

/// Retention policy for a single table.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetentionRule {
    /// Table name to apply the policy to.
    pub table: String,
    /// Column containing the timestamp (e.g. "created_at").
    pub timestamp_column: String,
    /// Maximum age in days. Rows older than this are purged.
    pub max_age_days: u32,
}

/// A completed snapshot record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SnapshotRecord {
    pub id: String,
    pub path: String,
    pub size_bytes: i64,
    pub checksum: String,
    pub created_at: String,
    pub node: String,
}

/// Org export package metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgExportMeta {
    pub org_id: String,
    pub org_name: String,
    pub exported_at: String,
    pub node: String,
    pub tables: Vec<String>,
    pub row_counts: Vec<(String, i64)>,
    pub version: String,
}

/// Purge event — emitted after auto-purge runs.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PurgeEvent {
    pub table: String,
    pub rows_deleted: i64,
    pub cutoff_date: String,
    pub executed_at: String,
}

/// Default retention rules per spec.
pub fn default_retention_rules() -> Vec<RetentionRule> {
    vec![
        RetentionRule {
            table: "audit_log".into(),
            timestamp_column: "created_at".into(),
            max_age_days: 365,
        },
        RetentionRule {
            table: "ipc_messages".into(),
            timestamp_column: "created_at".into(),
            max_age_days: 30,
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_rules_cover_required_tables() {
        let rules = default_retention_rules();
        assert_eq!(rules.len(), 2);
        assert_eq!(rules[0].table, "audit_log");
        assert_eq!(rules[0].max_age_days, 365);
        assert_eq!(rules[1].table, "ipc_messages");
        assert_eq!(rules[1].max_age_days, 30);
    }

    #[test]
    fn snapshot_record_serializes() {
        let rec = SnapshotRecord {
            id: "snap-001".into(),
            path: "/tmp/backup.db".into(),
            size_bytes: 1024,
            checksum: "abc123".into(),
            created_at: "2026-04-03T00:00:00Z".into(),
            node: "m5max".into(),
        };
        let json = serde_json::to_string(&rec).unwrap();
        assert!(json.contains("snap-001"));
    }

    #[test]
    fn purge_event_serializes() {
        let ev = PurgeEvent {
            table: "audit_log".into(),
            rows_deleted: 42,
            cutoff_date: "2025-04-03".into(),
            executed_at: "2026-04-03T00:00:00Z".into(),
        };
        let json = serde_json::to_string(&ev).unwrap();
        assert!(json.contains("audit_log"));
        assert!(json.contains("42"));
    }
}
