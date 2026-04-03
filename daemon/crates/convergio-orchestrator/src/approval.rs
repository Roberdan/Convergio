// Approval UX — reason codes, batch approval, cache for skip-if-seen.

use rusqlite::{params, Connection};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReasonCode {
    RiskLevel,
    FileScope,
    SecurityImpact,
    BreakingChange,
}

impl ReasonCode {
    fn as_str(&self) -> &'static str {
        match self {
            Self::RiskLevel => "risk_level",
            Self::FileScope => "file_scope",
            Self::SecurityImpact => "security_impact",
            Self::BreakingChange => "breaking_change",
        }
    }
}

#[derive(Debug, Clone)]
pub struct ApprovalRequest {
    pub reason_code: ReasonCode,
    pub task_id: String,
    pub description: String,
    pub previously_approved: bool,
}

#[derive(Debug, Clone)]
pub struct TaskInfo {
    pub task_type: String,
    pub effort: String,
    pub files: Vec<String>,
}

/// Infer the most relevant approval reason from task metadata.
/// Priority: SecurityImpact > BreakingChange > FileScope > RiskLevel.
pub fn classify_reason(task: &TaskInfo) -> ReasonCode {
    let lower = task.task_type.to_lowercase();

    if lower.contains("security") || lower.contains("auth") || lower.contains("crypto") {
        return ReasonCode::SecurityImpact;
    }
    if lower.contains("breaking") || lower.contains("migration") || lower.contains("schema") {
        return ReasonCode::BreakingChange;
    }
    let large_effort = matches!(task.effort.as_str(), "L" | "XL");
    let many_files = task.files.len() >= 5;
    if large_effort || many_files {
        return ReasonCode::FileScope;
    }
    ReasonCode::RiskLevel
}

/// Return `true` if this (reason_code, task_type) pair was approved before.
pub fn check_approval_cache(conn: &Connection, reason_code: &ReasonCode, task_type: &str) -> bool {
    conn.query_row(
        "SELECT 1 FROM approval_cache WHERE reason_code = ?1 AND task_type = ?2 LIMIT 1",
        params![reason_code.as_str(), task_type],
        |_| Ok(true),
    )
    .unwrap_or(false)
}

/// Persist an approval so future identical patterns are auto-approved.
pub fn record_approval(
    conn: &Connection,
    reason_code: &ReasonCode,
    task_type: &str,
    approved_by: &str,
) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT OR REPLACE INTO approval_cache (reason_code, task_type, approved_by) VALUES (?1, ?2, ?3)",
        params![reason_code.as_str(), task_type, approved_by],
    )?;
    Ok(())
}

/// Approve multiple tasks at once (all-or-nothing transaction).
pub fn approve_batch(conn: &Connection, task_ids: &[&str], approved_by: &str) -> rusqlite::Result<()> {
    conn.execute_batch("BEGIN")?;
    for task_id in task_ids {
        conn.execute(
            "INSERT OR REPLACE INTO batch_approvals (task_id, approved_by) VALUES (?1, ?2)",
            params![task_id, approved_by],
        )?;
    }
    conn.execute_batch("COMMIT")?;
    Ok(())
}

/// Build an ApprovalRequest for a task, consulting the cache.
pub fn build_request(
    conn: &Connection,
    task: &TaskInfo,
    task_id: impl Into<String>,
    description: impl Into<String>,
) -> ApprovalRequest {
    let reason_code = classify_reason(task);
    let previously_approved = check_approval_cache(conn, &reason_code, &task.task_type);
    ApprovalRequest {
        reason_code,
        task_id: task_id.into(),
        description: description.into(),
        previously_approved,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() { conn.execute_batch(m.up).unwrap(); }
        conn
    }

    fn task(task_type: &str, effort: &str, files: usize) -> TaskInfo {
        TaskInfo {
            task_type: task_type.to_string(),
            effort: effort.to_string(),
            files: (0..files).map(|i| format!("file{i}.rs")).collect(),
        }
    }

    #[test]
    fn classify_security() {
        assert_eq!(classify_reason(&task("security_audit", "S", 1)), ReasonCode::SecurityImpact);
    }

    #[test]
    fn classify_breaking() {
        assert_eq!(classify_reason(&task("breaking_api_change", "M", 2)), ReasonCode::BreakingChange);
    }

    #[test]
    fn classify_file_scope() {
        assert_eq!(classify_reason(&task("feature", "L", 1)), ReasonCode::FileScope);
        assert_eq!(classify_reason(&task("feature", "S", 5)), ReasonCode::FileScope);
    }

    #[test]
    fn classify_risk_default() {
        assert_eq!(classify_reason(&task("feature", "S", 1)), ReasonCode::RiskLevel);
    }

    #[test]
    fn cache_miss_then_hit() {
        let conn = setup();
        assert!(!check_approval_cache(&conn, &ReasonCode::RiskLevel, "feature"));
        record_approval(&conn, &ReasonCode::RiskLevel, "feature", "alice").unwrap();
        assert!(check_approval_cache(&conn, &ReasonCode::RiskLevel, "feature"));
    }

    #[test]
    fn approve_batch_works() {
        let conn = setup();
        approve_batch(&conn, &["T1", "T2", "T3"], "alice").unwrap();
        let count: i64 = conn.query_row("SELECT COUNT(*) FROM batch_approvals", [], |r| r.get(0)).unwrap();
        assert_eq!(count, 3);
    }

    #[test]
    fn build_request_previously_approved() {
        let conn = setup();
        let t = task("feature", "S", 1);
        record_approval(&conn, &ReasonCode::RiskLevel, "feature", "alice").unwrap();
        let req = build_request(&conn, &t, "T-42", "some desc");
        assert!(req.previously_approved);
    }
}
