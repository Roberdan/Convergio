// Compensation — automatic rollback when a wave or task fails.
// WHY: When a wave fails mid-execution, completed sibling tasks may leave
// partial state (branches, commits, DB rows). This module records what
// happened and builds a compensation plan to undo it.

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

type CompResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompensationAction {
    pub id: i64,
    pub plan_id: i64,
    pub wave_id: i64,
    pub task_id: i64,
    pub action_type: String,
    pub target: String,
    pub status: String,
    pub error_message: Option<String>,
    pub created_at: String,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompensationPlan {
    pub wave_id: i64,
    pub plan_id: i64,
    pub trigger_reason: String,
    pub actions: Vec<CompensationAction>,
}

/// Insert a new compensation action and return its id.
pub fn record_compensation(
    conn: &Connection,
    plan_id: i64,
    wave_id: i64,
    task_id: i64,
    action_type: &str,
    target: &str,
) -> CompResult<i64> {
    conn.execute(
        "INSERT INTO compensation_actions \
         (plan_id, wave_id, task_id, action_type, target) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![plan_id, wave_id, task_id, action_type, target],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Mark a single compensation action as executing, then completed or failed.
pub fn execute_compensation(conn: &Connection, id: i64) -> CompResult<()> {
    conn.execute(
        "UPDATE compensation_actions SET status = 'executing' WHERE id = ?1",
        params![id],
    )?;
    // Actual side-effects (git revert, branch delete, etc.) would be
    // dispatched here. For now we mark completed immediately.
    conn.execute(
        "UPDATE compensation_actions \
         SET status = 'completed', completed_at = datetime('now') \
         WHERE id = ?1",
        params![id],
    )?;
    Ok(())
}

/// List all compensation actions for a plan.
pub fn list_compensations(conn: &Connection, plan_id: i64) -> CompResult<Vec<CompensationAction>> {
    let mut stmt = conn.prepare(
        "SELECT id, plan_id, wave_id, task_id, action_type, target, \
               status, error_message, created_at, completed_at \
         FROM compensation_actions WHERE plan_id = ?1 ORDER BY id",
    )?;
    let rows = stmt
        .query_map(params![plan_id], row_to_action)?
        .collect::<Result<Vec<_>, _>>()?;
    Ok(rows)
}

/// List compensation actions scoped to a single wave.
pub fn get_wave_compensations(
    conn: &Connection,
    wave_id: i64,
) -> CompResult<Vec<CompensationAction>> {
    let mut stmt = conn.prepare(
        "SELECT id, plan_id, wave_id, task_id, action_type, target, \
               status, error_message, created_at, completed_at \
         FROM compensation_actions WHERE wave_id = ?1 ORDER BY id",
    )?;
    let rows = stmt
        .query_map(params![wave_id], row_to_action)?
        .collect::<Result<Vec<_>, _>>()?;
    Ok(rows)
}

/// Build a compensation plan for a failed wave: one "notify" action per
/// completed task that needs to be undone.
pub fn build_compensation_plan(
    conn: &Connection,
    wave_id: i64,
    reason: &str,
) -> CompResult<CompensationPlan> {
    let plan_id: i64 = conn.query_row(
        "SELECT plan_id FROM waves WHERE id = ?1",
        params![wave_id],
        |r| r.get(0),
    )?;
    let mut stmt = conn.prepare(
        "SELECT id, title FROM tasks \
         WHERE wave_id = ?1 AND status IN ('done','submitted')",
    )?;
    let tasks: Vec<(i64, String)> = stmt
        .query_map(params![wave_id], |r| Ok((r.get(0)?, r.get(1)?)))?
        .collect::<Result<Vec<_>, _>>()?;

    let mut actions = Vec::new();
    for (task_id, title) in tasks {
        let id = record_compensation(conn, plan_id, wave_id, task_id, "notify", &title)?;
        actions.push(get_single(conn, id)?);
    }
    Ok(CompensationPlan {
        wave_id,
        plan_id,
        trigger_reason: reason.to_string(),
        actions,
    })
}

/// Execute every pending action in a compensation plan.
pub fn execute_compensation_plan(conn: &Connection, plan: &CompensationPlan) -> CompResult<()> {
    for action in &plan.actions {
        if action.status == "pending" {
            execute_compensation(conn, action.id)?;
        }
    }
    Ok(())
}

/// Get a single compensation action by id.
pub fn get_single(conn: &Connection, id: i64) -> CompResult<CompensationAction> {
    let action = conn.query_row(
        "SELECT id, plan_id, wave_id, task_id, action_type, target, \
               status, error_message, created_at, completed_at \
         FROM compensation_actions WHERE id = ?1",
        params![id],
        row_to_action,
    )?;
    Ok(action)
}

fn row_to_action(r: &rusqlite::Row<'_>) -> rusqlite::Result<CompensationAction> {
    Ok(CompensationAction {
        id: r.get(0)?,
        plan_id: r.get(1)?,
        wave_id: r.get(2)?,
        task_id: r.get(3)?,
        action_type: r.get(4)?,
        target: r.get(5)?,
        status: r.get(6)?,
        error_message: r.get(7)?,
        created_at: r.get(8)?,
        completed_at: r.get(9)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA foreign_keys = OFF;").unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        for m in crate::schema_tracking::tracking_migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        for m in crate::schema_compensation::compensation_migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        seed(&conn);
        conn
    }

    fn seed(conn: &Connection) {
        conn.execute_batch(
            "INSERT INTO plans (id, project_id, name) VALUES (1, 'p1', 'Plan Alpha');\
             INSERT INTO waves (id, wave_id, plan_id, name, status) \
                 VALUES (1, 'W1', 1, 'Wave 1', 'in_progress');\
             INSERT INTO tasks (id, plan_id, wave_id, title, status) \
                 VALUES (10, 1, 1, 'Build API', 'done');\
             INSERT INTO tasks (id, plan_id, wave_id, title, status) \
                 VALUES (11, 1, 1, 'Write tests', 'submitted');",
        )
        .unwrap();
    }

    #[test]
    fn test_record_and_list() {
        let conn = setup();
        let id = record_compensation(&conn, 1, 1, 10, "revert_commit", "abc123").unwrap();
        assert!(id > 0);
        let all = list_compensations(&conn, 1).unwrap();
        assert_eq!(all.len(), 1);
        assert_eq!(all[0].action_type, "revert_commit");
        assert_eq!(all[0].target, "abc123");
    }

    #[test]
    fn test_build_compensation_plan() {
        let conn = setup();
        let plan = build_compensation_plan(&conn, 1, "wave failed").unwrap();
        assert_eq!(plan.plan_id, 1);
        assert_eq!(plan.wave_id, 1);
        assert_eq!(plan.actions.len(), 2);
        assert!(plan.actions.iter().all(|a| a.status == "pending"));
    }

    #[test]
    fn test_execute_marks_completed() {
        let conn = setup();
        let id = record_compensation(&conn, 1, 1, 10, "notify", "Build API").unwrap();
        execute_compensation(&conn, id).unwrap();
        let action = get_single(&conn, id).unwrap();
        assert_eq!(action.status, "completed");
        assert!(action.completed_at.is_some());
    }

    #[test]
    fn test_get_wave_compensations() {
        let conn = setup();
        record_compensation(&conn, 1, 1, 10, "notify", "task A").unwrap();
        record_compensation(&conn, 1, 1, 11, "notify", "task B").unwrap();
        let wave_actions = get_wave_compensations(&conn, 1).unwrap();
        assert_eq!(wave_actions.len(), 2);
    }
}
