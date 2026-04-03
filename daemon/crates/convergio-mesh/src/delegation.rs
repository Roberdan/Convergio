//! Delegation progress tracking.
//!
//! Records pipeline stages to delegation_progress table so
//! CLI/API can poll status of remote task delegations.

use tracing::{debug, warn};

/// Record a pipeline stage into the delegation_progress table.
/// Uses UPSERT so each delegation_id has exactly one row.
/// `step` goes into current_task, `status` must be running|blocked|done.
pub fn record_step(
    conn: &rusqlite::Connection,
    delegation_id: &str,
    step: &str,
    status: &str,
    summary: Option<&str>,
) {
    let sql = "INSERT INTO delegation_progress
         (delegation_id, status, current_task, output_summary, updated_at)
     VALUES (?1, ?2, ?3, ?4, datetime('now'))
     ON CONFLICT(delegation_id) DO UPDATE SET
         status         = excluded.status,
         current_task   = excluded.current_task,
         output_summary = COALESCE(excluded.output_summary, output_summary),
         updated_at     = excluded.updated_at";
    match conn.execute(sql, rusqlite::params![delegation_id, status, step, summary]) {
        Ok(_) => debug!(delegation_id, step, status, "progress recorded"),
        Err(e) => warn!(delegation_id, step, "progress insert failed: {e}"),
    }
}

/// Query current delegation progress.
pub fn get_progress(
    conn: &rusqlite::Connection,
    delegation_id: &str,
) -> Option<(String, String, Option<String>)> {
    conn.query_row(
        "SELECT status, current_task, output_summary \
         FROM delegation_progress WHERE delegation_id = ?1",
        rusqlite::params![delegation_id],
        |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, Option<String>>(2)?,
            ))
        },
    )
    .ok()
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    fn setup_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE delegation_progress (
                 id              INTEGER PRIMARY KEY,
                 delegation_id   TEXT NOT NULL UNIQUE,
                 status          TEXT NOT NULL DEFAULT 'running',
                 current_task    TEXT,
                 output_summary  TEXT,
                 updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
             );",
        )
        .unwrap();
        conn
    }

    #[test]
    fn record_and_query() {
        let conn = setup_db();
        record_step(&conn, "del-1", "connecting", "running", None);
        let (status, task, _) = get_progress(&conn, "del-1").unwrap();
        assert_eq!(status, "running");
        assert_eq!(task, "connecting");
    }

    #[test]
    fn upsert_updates_existing() {
        let conn = setup_db();
        record_step(&conn, "del-2", "connecting", "running", None);
        record_step(
            &conn,
            "del-2",
            "executing",
            "running",
            Some("started agent"),
        );
        let (_, task, summary) = get_progress(&conn, "del-2").unwrap();
        assert_eq!(task, "executing");
        assert_eq!(summary.as_deref(), Some("started agent"));
    }

    #[test]
    fn query_nonexistent_returns_none() {
        let conn = setup_db();
        assert!(get_progress(&conn, "nope").is_none());
    }
}
