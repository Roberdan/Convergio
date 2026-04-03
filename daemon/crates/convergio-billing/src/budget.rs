//! Budget hierarchy: platform -> org -> agent.
//!
//! Budgets never inherit upward. An agent cannot exceed its org budget,
//! and an org cannot exceed the platform budget.

use rusqlite::{params, Connection};

use crate::metering;
use crate::types::{BudgetConfig, BudgetScope, BudgetStatus};

/// Set or update a budget configuration.
pub fn set_budget(conn: &Connection, config: &BudgetConfig) -> rusqlite::Result<()> {
    let scope_str = match config.scope {
        BudgetScope::Platform => "platform",
        BudgetScope::Org => "org",
        BudgetScope::Agent => "agent",
    };
    conn.execute(
        "INSERT OR REPLACE INTO billing_budgets
         (scope, entity_id, daily_limit_usd, monthly_limit_usd, auto_pause)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            scope_str,
            config.entity_id,
            config.daily_limit_usd,
            config.monthly_limit_usd,
            config.auto_pause as i32,
        ],
    )?;
    Ok(())
}

/// Get current budget status for an entity.
pub fn get_status(conn: &Connection, entity_id: &str) -> rusqlite::Result<Option<BudgetStatus>> {
    let row = conn.query_row(
        "SELECT scope, entity_id, daily_limit_usd, monthly_limit_usd, auto_pause, paused
         FROM billing_budgets WHERE entity_id = ?1",
        params![entity_id],
        |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, f64>(2)?,
                r.get::<_, f64>(3)?,
                r.get::<_, bool>(4)?,
                r.get::<_, bool>(5)?,
            ))
        },
    );

    match row {
        Ok((scope_str, eid, daily_limit, monthly_limit, auto_pause, paused)) => {
            let scope = scope_from_str(&scope_str);
            let (daily_spent, monthly_spent) = spending_for_entity(conn, &scope, &eid)?;
            let daily_pct = pct(daily_spent, daily_limit);
            let monthly_pct = pct(monthly_spent, monthly_limit);
            Ok(Some(BudgetStatus {
                entity_id: eid,
                scope,
                daily_limit,
                monthly_limit,
                daily_spent,
                monthly_spent,
                daily_pct,
                monthly_pct,
                auto_pause,
                paused,
            }))
        }
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e),
    }
}

/// Check if an entity is over budget (should be paused).
pub fn is_over_budget(conn: &Connection, entity_id: &str) -> rusqlite::Result<bool> {
    match get_status(conn, entity_id)? {
        Some(s) => Ok(s.daily_pct >= 100.0 || s.monthly_pct >= 100.0),
        None => Ok(false),
    }
}

/// Pause an entity (set paused=1).
pub fn pause_entity(conn: &Connection, entity_id: &str) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE billing_budgets SET paused = 1 WHERE entity_id = ?1",
        params![entity_id],
    )?;
    Ok(())
}

/// Unpause an entity.
pub fn unpause_entity(conn: &Connection, entity_id: &str) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE billing_budgets SET paused = 0 WHERE entity_id = ?1",
        params![entity_id],
    )?;
    Ok(())
}

fn spending_for_entity(
    conn: &Connection,
    scope: &BudgetScope,
    entity_id: &str,
) -> rusqlite::Result<(f64, f64)> {
    match scope {
        BudgetScope::Agent => {
            let d = metering::agent_cost_today(conn, entity_id).unwrap_or(0.0);
            let m = conn
                .query_row(
                    "SELECT COALESCE(SUM(cost_usd), 0.0) FROM billing_usage
                     WHERE agent_id = ?1 AND date(created_at) >= date('now','start of month')",
                    params![entity_id],
                    |r| r.get(0),
                )
                .unwrap_or(0.0);
            Ok((d, m))
        }
        _ => {
            let d = metering::org_cost_today(conn, entity_id).unwrap_or(0.0);
            let m = metering::org_cost_month(conn, entity_id).unwrap_or(0.0);
            Ok((d, m))
        }
    }
}

fn pct(spent: f64, limit: f64) -> f64 {
    if limit > 0.0 {
        (spent / limit) * 100.0
    } else {
        0.0
    }
}

fn scope_from_str(s: &str) -> BudgetScope {
    match s {
        "platform" => BudgetScope::Platform,
        "org" => BudgetScope::Org,
        "agent" => BudgetScope::Agent,
        _ => BudgetScope::Org,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::schema::migrations;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn set_and_get_budget() {
        let conn = setup();
        let config = BudgetConfig {
            scope: BudgetScope::Org,
            entity_id: "acme-corp".into(),
            daily_limit_usd: 100.0,
            monthly_limit_usd: 2000.0,
            auto_pause: true,
        };
        set_budget(&conn, &config).unwrap();
        let status = get_status(&conn, "acme-corp").unwrap().unwrap();
        assert_eq!(status.daily_limit, 100.0);
        assert_eq!(status.monthly_limit, 2000.0);
        assert!(status.auto_pause);
        assert!(!status.paused);
    }

    #[test]
    fn pause_and_unpause() {
        let conn = setup();
        set_budget(
            &conn,
            &BudgetConfig {
                scope: BudgetScope::Org,
                entity_id: "org1".into(),
                daily_limit_usd: 50.0,
                monthly_limit_usd: 500.0,
                auto_pause: false,
            },
        )
        .unwrap();
        pause_entity(&conn, "org1").unwrap();
        assert!(get_status(&conn, "org1").unwrap().unwrap().paused);
        unpause_entity(&conn, "org1").unwrap();
        assert!(!get_status(&conn, "org1").unwrap().unwrap().paused);
    }

    #[test]
    fn missing_entity_returns_none() {
        let conn = setup();
        assert!(get_status(&conn, "nonexistent").unwrap().is_none());
    }
}
