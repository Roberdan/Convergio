//! Checkpoint persistence — save and restore execution state.
//!
//! Each execution can save arbitrary JSON state. On resume, the last
//! checkpoint is loaded and passed back to the LongRunnable.

use rusqlite::{params, Connection};
use serde_json::Value;

use crate::types::LongRunResult;

/// Save a checkpoint for an execution. Replaces previous checkpoint.
pub fn save(conn: &Connection, execution_id: &str, state: &Value) -> LongRunResult<()> {
    let state_json = serde_json::to_string(state)?;
    // Remove old checkpoint, insert fresh
    conn.execute(
        "DELETE FROM lr_checkpoints WHERE execution_id = ?1",
        params![execution_id],
    )?;
    conn.execute(
        "INSERT INTO lr_checkpoints (execution_id, state) VALUES (?1, ?2)",
        params![execution_id, state_json],
    )?;
    // Update execution stage
    conn.execute(
        "UPDATE lr_executions SET stage = 'checkpointing', \
         updated_at = datetime('now') WHERE id = ?1",
        params![execution_id],
    )?;
    tracing::debug!(execution_id, "checkpoint saved");
    Ok(())
}

/// Load the most recent checkpoint for an execution.
pub fn load(conn: &Connection, execution_id: &str) -> LongRunResult<Option<Value>> {
    let mut stmt = conn.prepare(
        "SELECT state FROM lr_checkpoints \
         WHERE execution_id = ?1 ORDER BY id DESC LIMIT 1",
    )?;
    let result = stmt.query_row(params![execution_id], |row| row.get::<_, String>(0));
    match result {
        Ok(json_str) => {
            let val: Value = serde_json::from_str(&json_str)?;
            Ok(Some(val))
        }
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Remove all checkpoints for an execution (after completion).
pub fn clear(conn: &Connection, execution_id: &str) -> LongRunResult<usize> {
    let n = conn.execute(
        "DELETE FROM lr_checkpoints WHERE execution_id = ?1",
        params![execution_id],
    )?;
    Ok(n)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

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
    fn save_and_load_roundtrip() {
        let conn = setup();
        let state = json!({"wave": 2, "tasks_done": 5});
        save(&conn, "e1", &state).unwrap();
        let loaded = load(&conn, "e1").unwrap().unwrap();
        assert_eq!(loaded["wave"], 2);
        assert_eq!(loaded["tasks_done"], 5);
    }

    #[test]
    fn load_missing_returns_none() {
        let conn = setup();
        assert!(load(&conn, "nonexistent").unwrap().is_none());
    }

    #[test]
    fn save_replaces_previous() {
        let conn = setup();
        save(&conn, "e1", &json!({"v": 1})).unwrap();
        save(&conn, "e1", &json!({"v": 2})).unwrap();
        let loaded = load(&conn, "e1").unwrap().unwrap();
        assert_eq!(loaded["v"], 2);
    }

    #[test]
    fn clear_removes_all() {
        let conn = setup();
        save(&conn, "e1", &json!({})).unwrap();
        let n = clear(&conn, "e1").unwrap();
        assert_eq!(n, 1);
        assert!(load(&conn, "e1").unwrap().is_none());
    }
}
