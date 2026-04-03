//! Concurrency control — parallel independent tasks, serialized dependencies.
//!
//! Wave ordering enforced: tasks in the same wave run in parallel,
//! but waves execute sequentially. Deadlock prevention via circular
//! dependency detection.

use rusqlite::{params, Connection};

use crate::types::RuntimeResult;

/// Check if a task can run: all dependencies (prior waves) must be done.
/// Returns true if the task is unblocked.
pub fn can_run(conn: &Connection, task_id: i64, plan_id: i64) -> RuntimeResult<bool> {
    // A task can run if all tasks in earlier waves are done
    let blocked: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks t1 \
         JOIN waves w1 ON t1.wave_id = w1.id \
         JOIN waves w2 ON w2.plan_id = w1.plan_id \
         JOIN tasks t2 ON t2.wave_id = w2.id \
         WHERE t2.id = ?1 AND w1.plan_id = ?2 \
         AND w1.id < w2.id \
         AND t1.status NOT IN ('done', 'skipped', 'cancelled')",
            params![task_id, plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    Ok(blocked == 0)
}

/// Count how many tasks in the same wave are currently in_progress.
/// Used for concurrency slot limiting.
pub fn wave_concurrency(conn: &Connection, wave_id: i64) -> RuntimeResult<usize> {
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks \
             WHERE wave_id = ?1 AND status = 'in_progress'",
            params![wave_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    Ok(count as usize)
}

/// Detect circular budget dependency between orgs.
/// Returns the cycle chain if detected.
pub fn detect_budget_cycle(
    conn: &Connection,
    from_org: &str,
    to_org: &str,
) -> RuntimeResult<Option<String>> {
    // Check if to_org already delegates budget back to from_org
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM art_delegations \
         WHERE from_org = ?1 AND to_org = ?2 AND returned = 0",
        params![to_org, from_org],
        |r| r.get(0),
    )?;

    if count > 0 {
        Ok(Some(format!("{from_org} -> {to_org} -> {from_org}")))
    } else {
        Ok(None)
    }
}

/// Autoscaling check: should we spawn additional executors?
/// Returns (should_scale_up, backlog_size, threshold).
pub fn autoscale_check(
    conn: &Connection,
    scale_up_threshold: usize,
    scale_down_idle_threshold: usize,
) -> RuntimeResult<AutoscaleDecision> {
    let backlog = crate::scheduler::queue_depth_total(conn)?;
    let active = active_agent_count(conn)?;

    if backlog > scale_up_threshold {
        Ok(AutoscaleDecision::ScaleUp {
            backlog,
            threshold: scale_up_threshold,
        })
    } else if active > 0 && backlog == 0 {
        // Check how many agents are idle (running but no task)
        let idle = idle_agent_count(conn)?;
        if idle > scale_down_idle_threshold {
            Ok(AutoscaleDecision::ScaleDown {
                idle,
                threshold: scale_down_idle_threshold,
            })
        } else {
            Ok(AutoscaleDecision::Steady)
        }
    } else {
        Ok(AutoscaleDecision::Steady)
    }
}

/// Autoscaling decision.
#[derive(Debug, Clone, Default, PartialEq, Eq, serde::Serialize)]
pub enum AutoscaleDecision {
    ScaleUp {
        backlog: usize,
        threshold: usize,
    },
    ScaleDown {
        idle: usize,
        threshold: usize,
    },
    #[default]
    Steady,
}

fn active_agent_count(conn: &Connection) -> RuntimeResult<usize> {
    let n: i64 = conn.query_row(
        "SELECT COUNT(*) FROM art_agents \
         WHERE stage IN ('running', 'borrowed')",
        [],
        |r| r.get(0),
    )?;
    Ok(n as usize)
}

fn idle_agent_count(conn: &Connection) -> RuntimeResult<usize> {
    let n: i64 = conn.query_row(
        "SELECT COUNT(*) FROM art_agents \
         WHERE stage = 'running' AND task_id IS NULL",
        [],
        |r| r.get(0),
    )?;
    Ok(n as usize)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::schema;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn detect_budget_cycle_none_when_clean() {
        let conn = setup();
        let cycle = detect_budget_cycle(&conn, "org-a", "org-b").unwrap();
        assert!(cycle.is_none());
    }

    #[test]
    fn detect_budget_cycle_found() {
        let conn = setup();
        // Insert agents and a delegation from org-b to org-a
        conn.execute(
            "INSERT INTO art_agents (id, agent_name, org_id, node, stage) \
             VALUES ('a1', 'elena', 'org-b', 'n1', 'running')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO art_delegations \
             (id, agent_id, from_org, to_org, budget_usd, expires_at) \
             VALUES ('d1', 'a1', 'org-b', 'org-a', 5.0, \
                     datetime('now', '+1 hour'))",
            [],
        )
        .unwrap();

        let cycle = detect_budget_cycle(&conn, "org-a", "org-b").unwrap();
        assert!(cycle.is_some());
        assert!(cycle.unwrap().contains("org-a"));
    }

    #[test]
    fn autoscale_steady_when_empty() {
        let conn = setup();
        let decision = autoscale_check(&conn, 10, 5).unwrap();
        assert_eq!(decision, AutoscaleDecision::Steady);
    }

    #[test]
    fn autoscale_up_when_backlog_high() {
        let conn = setup();
        // Enqueue many requests
        for i in 0..15 {
            let req = crate::types::SpawnRequest {
                agent_name: format!("agent-{i}"),
                org_id: "org-a".into(),
                task_id: None,
                capabilities: vec![],
                model_preference: None,
                budget_usd: 1.0,
                priority: 1,
            };
            crate::scheduler::enqueue(&conn, &req, Some(100)).unwrap();
        }
        let decision = autoscale_check(&conn, 10, 5).unwrap();
        assert!(matches!(decision, AutoscaleDecision::ScaleUp { .. }));
    }
}
