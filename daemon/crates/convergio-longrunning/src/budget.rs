//! Budget guard — stops execution when budget is exhausted.
//!
//! Tracks cost per execution and enforces limits. When spent >= limit,
//! the execution is paused and a BudgetExceeded error is returned.

use rusqlite::{params, Connection};

use crate::types::{LongRunError, LongRunResult};

/// Record cost for an execution and check budget.
///
/// Returns Ok(remaining) if within budget, or BudgetExceeded error if over.
pub fn record_cost(conn: &Connection, execution_id: &str, cost_usd: f64) -> LongRunResult<f64> {
    // Atomically update spent
    conn.execute(
        "UPDATE lr_executions SET spent_usd = spent_usd + ?1, \
         updated_at = datetime('now') WHERE id = ?2",
        params![cost_usd, execution_id],
    )?;

    // Check budget
    let (spent, budget): (f64, f64) = conn.query_row(
        "SELECT spent_usd, budget_usd FROM lr_executions WHERE id = ?1",
        params![execution_id],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;

    // budget_usd == 0 means unlimited
    if budget > 0.0 && spent >= budget {
        // Pause the execution
        conn.execute(
            "UPDATE lr_executions SET stage = 'paused', \
             updated_at = datetime('now') WHERE id = ?1",
            params![execution_id],
        )?;
        tracing::warn!(
            execution_id,
            spent,
            budget,
            "budget exhausted, execution paused"
        );
        return Err(LongRunError::BudgetExceeded {
            spent,
            limit: budget,
        });
    }

    let remaining = if budget > 0.0 {
        budget - spent
    } else {
        f64::INFINITY
    };
    Ok(remaining)
}

/// Get current budget status for an execution.
pub fn status(conn: &Connection, execution_id: &str) -> LongRunResult<(f64, f64)> {
    let result = conn.query_row(
        "SELECT spent_usd, budget_usd FROM lr_executions WHERE id = ?1",
        params![execution_id],
        |row| Ok((row.get(0)?, row.get(1)?)),
    );
    match result {
        Ok(pair) => Ok(pair),
        Err(rusqlite::Error::QueryReturnedNoRows) => {
            Err(LongRunError::NotFound(execution_id.to_string()))
        }
        Err(e) => Err(e.into()),
    }
}

/// Propagate budget from parent to child execution.
/// Child gets a fraction of the remaining parent budget.
pub fn propagate(
    conn: &Connection,
    parent_id: &str,
    child_id: &str,
    fraction: f64,
) -> LongRunResult<f64> {
    let (parent_spent, parent_budget) = status(conn, parent_id)?;
    let remaining = if parent_budget > 0.0 {
        (parent_budget - parent_spent).max(0.0)
    } else {
        0.0 // unlimited parent => child gets 0 (unlimited)
    };
    let child_budget = remaining * fraction.clamp(0.0, 1.0);
    conn.execute(
        "UPDATE lr_executions SET budget_usd = ?1, \
         updated_at = datetime('now') WHERE id = ?2",
        params![child_budget, child_id],
    )?;
    Ok(child_budget)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn record_cost_within_budget() {
        let conn = setup();
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node, budget_usd) \
             VALUES ('e1', 'a', 'n', 1.0)",
            [],
        )
        .unwrap();
        let remaining = record_cost(&conn, "e1", 0.3).unwrap();
        assert!((remaining - 0.7).abs() < 0.001);
    }

    #[test]
    fn record_cost_exceeds_budget() {
        let conn = setup();
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node, budget_usd) \
             VALUES ('e2', 'a', 'n', 0.5)",
            [],
        )
        .unwrap();
        let err = record_cost(&conn, "e2", 0.6).unwrap_err();
        assert!(err.to_string().contains("budget exceeded"));
    }

    #[test]
    fn unlimited_budget_always_ok() {
        let conn = setup();
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node, budget_usd) \
             VALUES ('e3', 'a', 'n', 0.0)",
            [],
        )
        .unwrap();
        let remaining = record_cost(&conn, "e3", 100.0).unwrap();
        assert!(remaining.is_infinite());
    }

    #[test]
    fn propagate_budget_to_child() {
        let conn = setup();
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node, budget_usd) \
             VALUES ('parent', 'a', 'n', 10.0)",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node, parent_id) \
             VALUES ('child', 'b', 'n', 'parent')",
            [],
        )
        .unwrap();
        let child_budget = propagate(&conn, "parent", "child", 0.5).unwrap();
        assert!((child_budget - 5.0).abs() < 0.001);
    }

    #[test]
    fn status_not_found() {
        let conn = setup();
        let err = status(&conn, "nope").unwrap_err();
        assert!(err.to_string().contains("nope"));
    }
}
