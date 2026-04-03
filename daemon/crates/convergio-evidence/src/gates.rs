// Hard mechanical enforcement gates — TestGate + ValidatorGate + ChecklistGate.
// WHY: "done" must be backed by evidence. No evidence = no transition.
// These gates are framework-agnostic: evidence is posted by the executor.

use crate::evidence::has_evidence;
use crate::types::{default_closure_checklist, GateViolation};
use rusqlite::{params, Connection};

/// Block status=submitted when no test_pass evidence has been recorded.
///
/// Executors MUST record test_pass evidence before transitioning to submitted.
pub fn run_test_gate(conn: &Connection, task_id: i64) -> Result<(), GateViolation> {
    if has_evidence(conn, task_id, "test_pass") {
        return Ok(());
    }
    Err(GateViolation {
        gate: "TestGate".into(),
        task_id,
        detail: format!(
            "no test evidence recorded for task {task_id}. \
             Record evidence_type='test_pass' first."
        ),
    })
}

/// Block status=done when no passing Thor verdict exists for this task.
///
/// Flow: executor -> submitted -> Thor validates -> verdict -> done.
pub fn run_validator_gate(conn: &Connection, task_id: i64) -> Result<(), GateViolation> {
    let pass_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM validation_verdicts v \
             JOIN validation_queue q ON v.queue_id = q.id \
             WHERE q.task_id = ?1 AND v.verdict = 'pass'",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    if pass_count > 0 {
        return Ok(());
    }

    Err(GateViolation {
        gate: "ValidatorGate".into(),
        task_id,
        detail: format!(
            "no passing Thor verdict for task {task_id}. \
             Task must be validated by Thor before transitioning to done."
        ),
    })
}

/// Enforce the closure checklist before accepting task=done.
/// Verifies that all required evidence types have been recorded.
pub fn run_checklist_gate(conn: &Connection, task_id: i64) -> Result<(), GateViolation> {
    let checklist = default_closure_checklist();
    let mut missing = Vec::new();

    for item in &checklist {
        if item.required && !has_evidence(conn, task_id, &item.evidence_type) {
            missing.push(item.name.clone());
        }
    }

    if missing.is_empty() {
        return Ok(());
    }

    Err(GateViolation {
        gate: "ChecklistGate".into(),
        task_id,
        detail: format!(
            "missing required evidence for task {task_id}: {}",
            missing.join(", ")
        ),
    })
}

/// Run all gates for a status transition. Returns first violation found.
pub fn run_all_gates(
    conn: &Connection,
    task_id: i64,
    target_status: &str,
) -> Result<(), GateViolation> {
    match target_status {
        "submitted" => run_test_gate(conn, task_id),
        "done" => {
            run_checklist_gate(conn, task_id)?;
            run_validator_gate(conn, task_id)
        }
        _ => Ok(()),
    }
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
        conn.execute(
            "INSERT INTO plans(id, project_id, name) VALUES (1, 'p', 'plan')",
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
    fn test_gate_blocks_without_evidence() {
        let conn = setup();
        let result = run_test_gate(&conn, 1);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().gate, "TestGate");
    }

    #[test]
    fn test_gate_passes_with_evidence() {
        let conn = setup();
        crate::evidence::record_evidence(&conn, 1, "test_pass", "cargo test", "ok", 0).unwrap();
        assert!(run_test_gate(&conn, 1).is_ok());
    }

    #[test]
    fn validator_gate_blocks_without_verdict() {
        let conn = setup();
        let result = run_validator_gate(&conn, 1);
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().gate, "ValidatorGate");
    }

    #[test]
    fn validator_gate_passes_with_verdict() {
        let conn = setup();
        conn.execute(
            "INSERT INTO validation_queue(id, task_id, status) VALUES (1, 1, 'completed')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO validation_verdicts(queue_id, verdict) VALUES (1, 'pass')",
            [],
        )
        .unwrap();
        assert!(run_validator_gate(&conn, 1).is_ok());
    }

    #[test]
    fn checklist_gate_blocks_missing_evidence() {
        let conn = setup();
        let result = run_checklist_gate(&conn, 1);
        assert!(result.is_err());
        let violation = result.unwrap_err();
        assert_eq!(violation.gate, "ChecklistGate");
        assert!(violation.detail.contains("tests_passed"));
    }

    #[test]
    fn checklist_gate_passes_with_all_evidence() {
        let conn = setup();
        crate::evidence::record_evidence(&conn, 1, "test_pass", "t", "ok", 0).unwrap();
        crate::evidence::record_evidence(&conn, 1, "build_pass", "b", "ok", 0).unwrap();
        crate::evidence::record_evidence(&conn, 1, "commit_hash", "abc", "", 0).unwrap();
        assert!(run_checklist_gate(&conn, 1).is_ok());
    }

    #[test]
    fn run_all_gates_submitted() {
        let conn = setup();
        assert!(run_all_gates(&conn, 1, "submitted").is_err());
        crate::evidence::record_evidence(&conn, 1, "test_pass", "t", "ok", 0).unwrap();
        assert!(run_all_gates(&conn, 1, "submitted").is_ok());
    }

    #[test]
    fn run_all_gates_pending_always_passes() {
        let conn = setup();
        assert!(run_all_gates(&conn, 1, "pending").is_ok());
    }
}
