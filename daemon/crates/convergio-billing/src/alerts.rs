//! Cost alerts — configurable thresholds with auto-pause.
//!
//! Checks budget utilization and triggers alerts at 70%, 85%, 95%.
//! When auto_pause is enabled and usage >= 100%, the entity is paused.

use rusqlite::Connection;

use crate::budget;
use crate::types::{AlertLevel, BudgetStatus, CostAlert};

/// Check if an entity has crossed alert thresholds.
/// Returns an alert if a threshold is breached, None otherwise.
pub fn check_thresholds(conn: &Connection, entity_id: &str) -> rusqlite::Result<Option<CostAlert>> {
    let status = match budget::get_status(conn, entity_id)? {
        Some(s) => s,
        None => return Ok(None),
    };

    let max_pct = status.daily_pct.max(status.monthly_pct);
    let alert = classify_alert(&status, max_pct);

    if let Some(mut a) = alert {
        // Auto-pause if enabled and over 100%
        if status.auto_pause && max_pct >= 100.0 {
            budget::pause_entity(conn, entity_id)?;
            a.auto_paused = true;
        }
        Ok(Some(a))
    } else {
        Ok(None)
    }
}

/// Check all entities for alerts. Returns all triggered alerts.
pub fn check_all_alerts(conn: &Connection) -> rusqlite::Result<Vec<CostAlert>> {
    let mut stmt = conn.prepare("SELECT entity_id FROM billing_budgets")?;
    let entity_ids: Vec<String> = stmt
        .query_map([], |row| row.get(0))?
        .filter_map(|r| r.ok())
        .collect();

    let mut alerts = Vec::new();
    for eid in entity_ids {
        if let Some(alert) = check_thresholds(conn, &eid)? {
            alerts.push(alert);
        }
    }
    Ok(alerts)
}

fn classify_alert(status: &BudgetStatus, max_pct: f64) -> Option<CostAlert> {
    let (level, msg) = if max_pct >= 95.0 {
        (
            AlertLevel::Critical,
            format!(
                "CRITICAL: {} at {:.0}% — budget nearly exhausted",
                status.entity_id, max_pct
            ),
        )
    } else if max_pct >= 85.0 {
        (
            AlertLevel::High,
            format!(
                "HIGH: {} at {:.0}% — approaching limit",
                status.entity_id, max_pct
            ),
        )
    } else if max_pct >= 70.0 {
        (
            AlertLevel::Warning,
            format!(
                "WARNING: {} at {:.0}% — monitor spending",
                status.entity_id, max_pct
            ),
        )
    } else {
        return None;
    };

    Some(CostAlert {
        entity_id: status.entity_id.clone(),
        scope: status.scope.clone(),
        level,
        usage_pct: max_pct,
        message: msg,
        auto_paused: false,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::budget::set_budget;
    use crate::schema::migrations;
    use crate::types::{BudgetConfig, BudgetScope};

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    fn seed_with_spending(conn: &rusqlite::Connection, org: &str, cost: f64) {
        set_budget(
            conn,
            &BudgetConfig {
                scope: BudgetScope::Org,
                entity_id: org.into(),
                daily_limit_usd: 100.0,
                monthly_limit_usd: 100.0,
                auto_pause: false,
            },
        )
        .unwrap();
        conn.execute(
            "INSERT INTO billing_usage (org_id, category, quantity, unit, cost_usd)
             VALUES (?1, 'api_call', 1.0, 'unit', ?2)",
            rusqlite::params![org, cost],
        )
        .unwrap();
    }

    #[test]
    fn no_alert_below_70pct() {
        let conn = setup();
        seed_with_spending(&conn, "org-low", 60.0);
        assert!(check_thresholds(&conn, "org-low").unwrap().is_none());
    }

    #[test]
    fn warning_at_75pct() {
        let conn = setup();
        seed_with_spending(&conn, "org-warn", 75.0);
        let alert = check_thresholds(&conn, "org-warn").unwrap().unwrap();
        assert_eq!(alert.level, AlertLevel::Warning);
    }

    #[test]
    fn critical_at_96pct() {
        let conn = setup();
        seed_with_spending(&conn, "org-crit", 96.0);
        let alert = check_thresholds(&conn, "org-crit").unwrap().unwrap();
        assert_eq!(alert.level, AlertLevel::Critical);
    }

    #[test]
    fn auto_pause_when_over_100pct() {
        let conn = setup();
        set_budget(
            &conn,
            &BudgetConfig {
                scope: BudgetScope::Org,
                entity_id: "org-over".into(),
                daily_limit_usd: 100.0,
                monthly_limit_usd: 100.0,
                auto_pause: true,
            },
        )
        .unwrap();
        conn.execute(
            "INSERT INTO billing_usage (org_id, category, quantity, unit, cost_usd)
             VALUES ('org-over', 'api_call', 1.0, 'unit', 105.0)",
            [],
        )
        .unwrap();
        let alert = check_thresholds(&conn, "org-over").unwrap().unwrap();
        assert!(alert.auto_paused);
        let status = budget::get_status(&conn, "org-over").unwrap().unwrap();
        assert!(status.paused);
    }
}
