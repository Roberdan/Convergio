// Evidence recording and querying.
// WHY: "done" must be backed by verifiable evidence — not just "posted".

use crate::types::{CommitTaskMatch, EvidenceKind, EvidenceRecord};
use rusqlite::{params, Connection};

/// Record evidence for a task. Validates evidence_type against allowlist.
pub fn record_evidence(
    conn: &Connection,
    task_id: i64,
    evidence_type: &str,
    command: &str,
    output_summary: &str,
    exit_code: i64,
) -> Result<i64, String> {
    EvidenceKind::parse(evidence_type)
        .ok_or_else(|| format!("unknown evidence_type '{evidence_type}'"))?;

    // Verify task exists
    let exists: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE id = ?1",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if exists == 0 {
        return Err(format!("task {task_id} not found"));
    }

    conn.execute(
        "INSERT INTO task_evidence \
         (task_db_id, evidence_type, command, output_summary, exit_code) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![task_id, evidence_type, command, output_summary, exit_code],
    )
    .map_err(|e| format!("insert evidence failed: {e}"))?;

    Ok(conn.last_insert_rowid())
}

/// Check if a task has at least one evidence row of the given type.
pub fn has_evidence(conn: &Connection, task_id: i64, evidence_type: &str) -> bool {
    conn.query_row(
        "SELECT COUNT(*) FROM task_evidence \
         WHERE task_db_id = ?1 AND evidence_type = ?2",
        params![task_id, evidence_type],
        |r| r.get::<_, i64>(0),
    )
    .unwrap_or(0)
        > 0
}

/// List all evidence records for a task.
pub fn list_evidence(conn: &Connection, task_id: i64) -> Vec<EvidenceRecord> {
    let mut stmt = match conn.prepare(
        "SELECT id, task_db_id, evidence_type, command, \
         output_summary, exit_code, created_at \
         FROM task_evidence WHERE task_db_id = ?1 ORDER BY id",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map(params![task_id], |r| {
        Ok(EvidenceRecord {
            id: r.get(0)?,
            task_id: r.get(1)?,
            evidence_type: r.get(2)?,
            command: r.get(3)?,
            output_summary: r.get(4)?,
            exit_code: r.get(5)?,
            created_at: r.get(6)?,
        })
    })
    .ok()
    .map(|rows| rows.filter_map(|r| r.ok()).collect())
    .unwrap_or_default()
}

/// Record a commit-to-task association. Idempotent (UNIQUE constraint).
pub fn record_commit_match(
    conn: &Connection,
    task_id: i64,
    commit_hash: &str,
    commit_message: &str,
) -> Result<(), String> {
    conn.execute(
        "INSERT OR IGNORE INTO commit_task_matches \
         (task_id, commit_hash, commit_message) VALUES (?1, ?2, ?3)",
        params![task_id, commit_hash, commit_message],
    )
    .map_err(|e| format!("record commit match failed: {e}"))?;
    Ok(())
}

/// List commit matches for a task.
pub fn list_commit_matches(conn: &Connection, task_id: i64) -> Vec<CommitTaskMatch> {
    let mut stmt = match conn.prepare(
        "SELECT id, task_id, commit_hash, commit_message, matched_at \
         FROM commit_task_matches WHERE task_id = ?1 ORDER BY id",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map(params![task_id], |r| {
        Ok(CommitTaskMatch {
            id: r.get(0)?,
            task_id: r.get(1)?,
            commit_hash: r.get(2)?,
            commit_message: r.get(3)?,
            matched_at: r.get(4)?,
        })
    })
    .ok()
    .map(|rows| rows.filter_map(|r| r.ok()).collect())
    .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in convergio_orchestrator::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        // Insert a task for testing
        conn.execute(
            "INSERT INTO plans(id, project_id, name) VALUES (1, 'proj', 'plan')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks(id, plan_id, status) VALUES (1, 1, 'in_progress')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn record_and_list_evidence() {
        let conn = setup();
        let id = record_evidence(&conn, 1, "test_pass", "cargo test", "ok", 0).unwrap();
        assert!(id > 0);
        let records = list_evidence(&conn, 1);
        assert_eq!(records.len(), 1);
        assert_eq!(records[0].evidence_type, "test_pass");
    }

    #[test]
    fn record_evidence_unknown_type() {
        let conn = setup();
        let err = record_evidence(&conn, 1, "magic", "cmd", "out", 0);
        assert!(err.is_err());
        assert!(err.unwrap_err().contains("unknown"));
    }

    #[test]
    fn record_evidence_task_not_found() {
        let conn = setup();
        let err = record_evidence(&conn, 999, "test_pass", "cmd", "out", 0);
        assert!(err.is_err());
        assert!(err.unwrap_err().contains("not found"));
    }

    #[test]
    fn has_evidence_works() {
        let conn = setup();
        assert!(!has_evidence(&conn, 1, "test_pass"));
        record_evidence(&conn, 1, "test_pass", "cargo test", "ok", 0).unwrap();
        assert!(has_evidence(&conn, 1, "test_pass"));
        assert!(!has_evidence(&conn, 1, "build_pass"));
    }

    #[test]
    fn commit_match_idempotent() {
        let conn = setup();
        record_commit_match(&conn, 1, "abc123", "feat: something").unwrap();
        record_commit_match(&conn, 1, "abc123", "feat: something").unwrap();
        let matches = list_commit_matches(&conn, 1);
        assert_eq!(matches.len(), 1);
    }
}
