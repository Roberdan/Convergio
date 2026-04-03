//! Heartbeat monitor — tracks liveness of long-running executions.
//!
//! Each execution registers its expected heartbeat interval. The monitor
//! updates `lr_heartbeats` on each beat. The reaper checks for stale entries.

use rusqlite::{params, Connection};

use crate::types::LongRunResult;

/// Register a new execution for heartbeat monitoring.
pub fn register(conn: &Connection, execution_id: &str, interval_secs: u64) -> LongRunResult<()> {
    conn.execute(
        "INSERT OR REPLACE INTO lr_heartbeats (execution_id, last_seen, interval_s) \
         VALUES (?1, datetime('now'), ?2)",
        params![execution_id, interval_secs as i64],
    )?;
    tracing::debug!(execution_id, interval_secs, "heartbeat registered");
    Ok(())
}

/// Record a heartbeat for an execution.
pub fn beat(conn: &Connection, execution_id: &str) -> LongRunResult<()> {
    let updated = conn.execute(
        "UPDATE lr_heartbeats SET last_seen = datetime('now') \
         WHERE execution_id = ?1",
        params![execution_id],
    )?;
    if updated == 0 {
        return Err(crate::types::LongRunError::NotFound(format!(
            "no heartbeat registration for {execution_id}"
        )));
    }
    Ok(())
}

/// Remove heartbeat tracking for a completed execution.
pub fn unregister(conn: &Connection, execution_id: &str) -> LongRunResult<()> {
    conn.execute(
        "DELETE FROM lr_heartbeats WHERE execution_id = ?1",
        params![execution_id],
    )?;
    Ok(())
}

/// Find executions whose heartbeat is stale (last_seen older than 3x interval).
/// Returns list of (execution_id, elapsed_secs, max_secs).
pub fn find_stale(conn: &Connection) -> LongRunResult<Vec<(String, u64, u64)>> {
    let mut stmt = conn.prepare(
        "SELECT execution_id, interval_s, \
         CAST((julianday('now') - julianday(last_seen)) * 86400 AS INTEGER) \
         AS elapsed_s \
         FROM lr_heartbeats \
         WHERE elapsed_s > (interval_s * 3)",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, i64>(1)?,
            row.get::<_, i64>(2)?,
        ))
    })?;
    let mut stale = Vec::new();
    for row in rows {
        let (id, interval, elapsed) = row?;
        let max = (interval * 3) as u64;
        stale.push((id, elapsed as u64, max));
    }
    Ok(stale)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node) VALUES ('e1', 'a', 'n')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn register_and_beat() {
        let conn = setup();
        register(&conn, "e1", 30).unwrap();
        beat(&conn, "e1").unwrap();
    }

    #[test]
    fn beat_unknown_errors() {
        let conn = setup();
        let err = beat(&conn, "nonexistent").unwrap_err();
        assert!(err.to_string().contains("no heartbeat registration"));
    }

    #[test]
    fn unregister_removes_entry() {
        let conn = setup();
        register(&conn, "e1", 30).unwrap();
        unregister(&conn, "e1").unwrap();
        let err = beat(&conn, "e1").unwrap_err();
        assert!(err.to_string().contains("no heartbeat"));
    }

    #[test]
    fn find_stale_empty_when_fresh() {
        let conn = setup();
        register(&conn, "e1", 30).unwrap();
        let stale = find_stale(&conn).unwrap();
        assert!(stale.is_empty(), "fresh heartbeat should not be stale");
    }
}
