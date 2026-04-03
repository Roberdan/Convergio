//! Metering — tracks every cost-generating action.
//!
//! Granularity: per-agent, per-task, per-org.
//! Every action has a category (api_call, token_inference, compute_time, storage).

use rusqlite::{params, Connection};

use crate::types::{ActionCategory, UsageRecord};

/// Record a usage event.
pub fn record_usage(conn: &Connection, record: &UsageRecord) -> rusqlite::Result<i64> {
    conn.execute(
        "INSERT INTO billing_usage
         (org_id, agent_id, task_id, category, quantity, unit, cost_usd, model, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        params![
            record.org_id,
            record.agent_id,
            record.task_id,
            record.category.to_string(),
            record.quantity,
            record.unit,
            record.cost_usd,
            record.model,
            record.created_at.to_rfc3339(),
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Total cost for an org today.
pub fn org_cost_today(conn: &Connection, org_id: &str) -> rusqlite::Result<f64> {
    conn.query_row(
        "SELECT COALESCE(SUM(cost_usd), 0.0) FROM billing_usage
         WHERE org_id = ?1 AND date(created_at) = date('now')",
        params![org_id],
        |r| r.get(0),
    )
}

/// Total cost for an org this month.
pub fn org_cost_month(conn: &Connection, org_id: &str) -> rusqlite::Result<f64> {
    conn.query_row(
        "SELECT COALESCE(SUM(cost_usd), 0.0) FROM billing_usage
         WHERE org_id = ?1 AND date(created_at) >= date('now', 'start of month')",
        params![org_id],
        |r| r.get(0),
    )
}

/// Total cost for a specific agent today.
pub fn agent_cost_today(conn: &Connection, agent_id: &str) -> rusqlite::Result<f64> {
    conn.query_row(
        "SELECT COALESCE(SUM(cost_usd), 0.0) FROM billing_usage
         WHERE agent_id = ?1 AND date(created_at) = date('now')",
        params![agent_id],
        |r| r.get(0),
    )
}

/// Usage records for an org in a date range.
pub fn usage_for_period(
    conn: &Connection,
    org_id: &str,
    from: &str,
    to: &str,
) -> rusqlite::Result<Vec<UsageRecord>> {
    let mut stmt = conn.prepare(
        "SELECT id, org_id, agent_id, task_id, category, quantity, unit,
                cost_usd, model, created_at
         FROM billing_usage
         WHERE org_id = ?1 AND date(created_at) BETWEEN ?2 AND ?3
         ORDER BY created_at",
    )?;
    let rows = stmt.query_map(params![org_id, from, to], |row| {
        Ok(UsageRecord {
            id: row.get(0)?,
            org_id: row.get(1)?,
            agent_id: row.get(2)?,
            task_id: row.get(3)?,
            category: ActionCategory::from_str_value(&row.get::<_, String>(4)?),
            quantity: row.get(5)?,
            unit: row.get(6)?,
            cost_usd: row.get(7)?,
            model: row.get(8)?,
            created_at: chrono::Utc::now(), // DB stores text, parse later
        })
    })?;
    rows.collect()
}

/// Usage grouped by category for an org in a period.
pub fn usage_by_category(
    conn: &Connection,
    org_id: &str,
    from: &str,
    to: &str,
) -> rusqlite::Result<Vec<(String, f64, f64)>> {
    let mut stmt = conn.prepare(
        "SELECT category, SUM(quantity), SUM(cost_usd) FROM billing_usage
         WHERE org_id = ?1 AND date(created_at) BETWEEN ?2 AND ?3
         GROUP BY category ORDER BY SUM(cost_usd) DESC",
    )?;
    let rows = stmt.query_map(params![org_id, from, to], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?))
    })?;
    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::schema::migrations;
    use chrono::Utc;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn record_and_query_usage() {
        let conn = setup();
        let rec = UsageRecord {
            id: None,
            org_id: "acme-corp".into(),
            agent_id: Some("elena".into()),
            task_id: Some(42),
            category: ActionCategory::TokenInference,
            quantity: 1500.0,
            unit: "tokens".into(),
            cost_usd: 0.045,
            model: Some("claude-opus".into()),
            created_at: Utc::now(),
        };
        let id = record_usage(&conn, &rec).unwrap();
        assert!(id > 0);
    }

    #[test]
    fn usage_by_category_groups_correctly() {
        let conn = setup();
        for cat in &["api_call", "token_inference", "api_call"] {
            conn.execute(
                "INSERT INTO billing_usage (org_id, category, quantity, unit, cost_usd)
                 VALUES ('org1', ?1, 1.0, 'unit', 10.0)",
                params![cat],
            )
            .unwrap();
        }
        let groups = usage_by_category(&conn, "org1", "2020-01-01", "2030-12-31").unwrap();
        assert_eq!(groups.len(), 2);
        // api_call should have higher total (20.0)
        assert_eq!(groups[0].0, "api_call");
    }
}
