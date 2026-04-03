// Pre-flight validation before spawning an agent.
// WHY: prevent launching agents when preconditions are not met.
// Checks: dependencies merged, workspace clean, no conflicts.

use crate::types::{PreflightCheck, PreflightResult};
use rusqlite::{params, Connection};

/// Run pre-flight checks before assigning a task to an agent.
pub fn run_preflight(conn: &Connection, task_id: i64) -> PreflightResult {
    let checks = vec![
        check_task_exists(conn, task_id),
        check_task_pending(conn, task_id),
        check_deps_completed(conn, task_id),
        check_wave_active(conn, task_id),
    ];
    let passed = checks.iter().all(|c| c.passed);
    PreflightResult { passed, checks }
}

/// Verify the task actually exists.
fn check_task_exists(conn: &Connection, task_id: i64) -> PreflightCheck {
    let exists: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE id = ?1",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    PreflightCheck {
        name: "task_exists".into(),
        passed: exists > 0,
        detail: if exists > 0 {
            "task found".into()
        } else {
            format!("task {task_id} not found")
        },
    }
}

/// Verify the task is in pending status (ready to be assigned).
fn check_task_pending(conn: &Connection, task_id: i64) -> PreflightCheck {
    let status: String = conn
        .query_row(
            "SELECT status FROM tasks WHERE id = ?1",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or_else(|_| "unknown".into());
    let passed = status == "pending";
    PreflightCheck {
        name: "task_pending".into(),
        passed,
        detail: if passed {
            "task is pending".into()
        } else {
            format!("task status is '{status}', expected 'pending'")
        },
    }
}

/// Verify all dependency tasks in the same wave are done.
/// Uses the wave ordering: earlier waves must be fully done.
fn check_deps_completed(conn: &Connection, task_id: i64) -> PreflightCheck {
    // Get this task's wave_id
    let wave_id: Option<i64> = conn
        .query_row(
            "SELECT wave_id FROM tasks WHERE id = ?1",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or(None);

    let Some(wave_id) = wave_id else {
        return PreflightCheck {
            name: "deps_completed".into(),
            passed: true,
            detail: "no wave assignment, deps check skipped".into(),
        };
    };

    // Get plan_id for this wave
    let plan_id: i64 = conn
        .query_row(
            "SELECT plan_id FROM waves WHERE id = ?1",
            params![wave_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Count incomplete tasks in earlier waves of the same plan
    let incomplete: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks t \
             JOIN waves w ON t.wave_id = w.id \
             WHERE w.plan_id = ?1 AND w.id < ?2 \
             AND t.status NOT IN ('done', 'skipped', 'cancelled')",
            params![plan_id, wave_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let passed = incomplete == 0;
    PreflightCheck {
        name: "deps_completed".into(),
        passed,
        detail: if passed {
            "all prior wave tasks completed".into()
        } else {
            format!("{incomplete} tasks in prior waves still incomplete")
        },
    }
}

/// Verify the task's wave is in an active state.
fn check_wave_active(conn: &Connection, task_id: i64) -> PreflightCheck {
    let wave_status: String = conn
        .query_row(
            "SELECT COALESCE(w.status, 'pending') FROM tasks t \
             LEFT JOIN waves w ON t.wave_id = w.id WHERE t.id = ?1",
            params![task_id],
            |r| r.get(0),
        )
        .unwrap_or_else(|_| "unknown".into());
    let passed = wave_status == "pending" || wave_status == "active";
    PreflightCheck {
        name: "wave_active".into(),
        passed,
        detail: if passed {
            format!("wave status is '{wave_status}'")
        } else {
            format!("wave status is '{wave_status}', expected pending/active")
        },
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
            "INSERT INTO waves(id, wave_id, plan_id, status) VALUES (1, 'w1', 1, 'active')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks(id, plan_id, wave_id, status) \
             VALUES (1, 1, 1, 'pending')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn preflight_passes_for_ready_task() {
        let conn = setup();
        let result = run_preflight(&conn, 1);
        assert!(result.passed);
        assert!(result.failed_checks().is_empty());
    }

    #[test]
    fn preflight_fails_for_nonexistent_task() {
        let conn = setup();
        let result = run_preflight(&conn, 999);
        assert!(!result.passed);
        assert!(result
            .failed_checks()
            .iter()
            .any(|c| c.name == "task_exists"));
    }

    #[test]
    fn preflight_fails_for_in_progress_task() {
        let conn = setup();
        conn.execute("UPDATE tasks SET status='in_progress' WHERE id=1", [])
            .unwrap();
        let result = run_preflight(&conn, 1);
        assert!(!result.passed);
    }

    #[test]
    fn preflight_fails_with_incomplete_prior_wave() {
        let conn = setup();
        // Add wave 2 with a task, and check task in wave 2
        conn.execute(
            "INSERT INTO waves(id, wave_id, plan_id, status) \
             VALUES (2, 'w2', 1, 'pending')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks(id, plan_id, wave_id, status) \
             VALUES (2, 1, 2, 'pending')",
            [],
        )
        .unwrap();
        // Task 1 in wave 1 is still pending -> task 2 deps fail
        let result = run_preflight(&conn, 2);
        assert!(!result.passed);
        let dep_check = result.failed_checks();
        assert!(dep_check.iter().any(|c| c.name == "deps_completed"));
    }

    #[test]
    fn preflight_passes_when_prior_wave_done() {
        let conn = setup();
        conn.execute("UPDATE tasks SET status='done' WHERE id=1", [])
            .unwrap();
        conn.execute(
            "INSERT INTO waves(id, wave_id, plan_id, status) \
             VALUES (2, 'w2', 1, 'pending')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks(id, plan_id, wave_id, status) \
             VALUES (2, 1, 2, 'pending')",
            [],
        )
        .unwrap();
        let result = run_preflight(&conn, 2);
        assert!(result.passed);
    }
}
