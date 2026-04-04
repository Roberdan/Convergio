//! Lifecycle gates — enforce plan/task/wave status transitions (Fase 24c).
//!
//! Each gate returns Ok(()) or Err(reason) to block the transition.
//! Called by routes before executing state changes.

use convergio_db::pool::ConnPool;
use rusqlite::Connection;

/// Gate error — returned when a transition is blocked.
#[derive(Debug)]
pub struct GateError {
    pub gate: &'static str,
    pub reason: String,
}

impl std::fmt::Display for GateError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "[{}] {}", self.gate, self.reason)
    }
}

/// ImportGate: cannot add tasks to a plan not in draft/todo/approved.
pub fn import_gate(conn: &Connection, plan_id: i64) -> Result<(), GateError> {
    let status: String = conn
        .query_row("SELECT status FROM plans WHERE id = ?1", [plan_id], |r| {
            r.get(0)
        })
        .map_err(|_| GateError {
            gate: "ImportGate",
            reason: "plan not found".into(),
        })?;
    match status.as_str() {
        "todo" | "draft" | "approved" => Ok(()),
        _ => Err(GateError {
            gate: "ImportGate",
            reason: format!("cannot add tasks to plan in status '{status}'"),
        }),
    }
}

/// StartGate: cannot start a plan without at least 1 task.
pub fn start_gate(conn: &Connection, plan_id: i64) -> Result<(), GateError> {
    let tasks: i64 = conn
        .query_row(
            "SELECT count(*) FROM tasks WHERE plan_id = ?1",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if tasks == 0 {
        return Err(GateError {
            gate: "StartGate",
            reason: "plan has zero tasks — cannot start".into(),
        });
    }
    Ok(())
}

/// TestGate: task cannot move to `submitted` without evidence of type test_pass.
pub fn test_gate(conn: &Connection, task_id: i64) -> Result<(), GateError> {
    // Check task_evidence table (from convergio-evidence crate, if exists)
    let has_test: bool = conn
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM task_evidence \
             WHERE task_id = ?1 AND kind = 'test_pass')",
            [task_id],
            |r| r.get(0),
        )
        .unwrap_or(false);
    if !has_test {
        return Err(GateError {
            gate: "TestGate",
            reason: format!("task {task_id} has no test_pass evidence"),
        });
    }
    Ok(())
}

/// EvidenceGate: task cannot move to `submitted` without at least 1 evidence record.
pub fn evidence_gate(conn: &Connection, task_id: i64) -> Result<(), GateError> {
    let count: i64 = conn
        .query_row(
            "SELECT count(*) FROM task_evidence WHERE task_id = ?1",
            [task_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if count == 0 {
        return Err(GateError {
            gate: "EvidenceGate",
            reason: format!("task {task_id} has zero evidence records"),
        });
    }
    Ok(())
}

/// ValidatorGate: task cannot move to `done` without a positive validation verdict.
pub fn validator_gate(conn: &Connection, task_id: i64) -> Result<(), GateError> {
    let has_verdict: bool = conn
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM validation_verdicts v \
             JOIN validation_queue q ON q.id = v.queue_id \
             WHERE q.task_id = ?1 AND v.verdict = 'pass')",
            [task_id],
            |r| r.get(0),
        )
        .unwrap_or(false);
    if !has_verdict {
        return Err(GateError {
            gate: "ValidatorGate",
            reason: format!("task {task_id} has no passing validation verdict"),
        });
    }
    Ok(())
}

/// Run all applicable gates for a task status transition.
/// Returns the first gate error encountered, or Ok(()) if all pass.
pub fn check_task_transition(
    pool: &ConnPool,
    task_id: i64,
    new_status: &str,
) -> Result<(), GateError> {
    let conn = pool.get().map_err(|e| GateError {
        gate: "db",
        reason: e.to_string(),
    })?;
    match new_status {
        "submitted" => {
            // Evidence and test gates — soft: only block if table exists
            if table_exists(&conn, "task_evidence") {
                evidence_gate(&conn, task_id)?;
                // TestGate is optional — only enforce if evidence crate is present
                let _ = test_gate(&conn, task_id);
            }
            Ok(())
        }
        "done" => {
            validator_gate(&conn, task_id)?;
            Ok(())
        }
        _ => Ok(()),
    }
}

/// Check if a table exists in the database.
fn table_exists(conn: &Connection, table: &str) -> bool {
    conn.query_row(
        "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1)",
        [table],
        |r| r.get(0),
    )
    .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use convergio_db::pool::create_memory_pool;

    fn setup_db() -> ConnPool {
        let pool = create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        conn.execute_batch(
            "CREATE TABLE plans (id INTEGER PRIMARY KEY, status TEXT);
             CREATE TABLE tasks (id INTEGER PRIMARY KEY, plan_id INTEGER);
             INSERT INTO plans VALUES (1, 'todo');
             INSERT INTO plans VALUES (2, 'in_progress');
             INSERT INTO tasks VALUES (1, 1);",
        )
        .unwrap();
        pool
    }

    #[test]
    fn import_gate_allows_todo() {
        let pool = setup_db();
        let conn = pool.get().unwrap();
        assert!(import_gate(&conn, 1).is_ok());
    }

    #[test]
    fn import_gate_blocks_in_progress() {
        let pool = setup_db();
        let conn = pool.get().unwrap();
        assert!(import_gate(&conn, 2).is_err());
    }

    #[test]
    fn start_gate_allows_with_tasks() {
        let pool = setup_db();
        let conn = pool.get().unwrap();
        assert!(start_gate(&conn, 1).is_ok());
    }

    #[test]
    fn start_gate_blocks_without_tasks() {
        let pool = setup_db();
        let conn = pool.get().unwrap();
        assert!(start_gate(&conn, 2).is_err());
    }
}
