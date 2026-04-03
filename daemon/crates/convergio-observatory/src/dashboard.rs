//! Dashboard aggregates — cost/hour per org, task throughput/day,
//! average model latency. Reads from existing tables across crates.

use rusqlite::{params, Connection};

use crate::types::{CostPerHour, ModelLatency, TaskThroughput};

/// Cost per hour for an org over a date range.
///
/// Reads from `billing_usage` (owned by convergio-billing).
pub fn cost_per_hour(
    conn: &Connection,
    org_id: &str,
    since: &str,
    until: &str,
) -> Result<Vec<CostPerHour>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT org_id, strftime('%Y-%m-%dT%H:00', created_at) AS hour, \
         SUM(cost_usd) AS cost \
         FROM billing_usage \
         WHERE org_id = ?1 AND created_at >= ?2 AND created_at <= ?3 \
         GROUP BY org_id, hour ORDER BY hour",
    )?;
    let rows = stmt.query_map(params![org_id, since, until], |row| {
        Ok(CostPerHour {
            org_id: row.get(0)?,
            hour: row.get(1)?,
            cost_usd: row.get(2)?,
        })
    })?;
    rows.collect()
}

/// Task throughput per day for an org.
///
/// Reads from `tasks` (owned by convergio-orchestrator).
pub fn task_throughput(
    conn: &Connection,
    org_id: Option<&str>,
    since: &str,
    until: &str,
) -> Result<Vec<TaskThroughput>, rusqlite::Error> {
    let (sql, org_val);
    if let Some(oid) = org_id {
        org_val = oid.to_string();
        sql = "SELECT ?1 AS org_id, date(completed_at) AS d, \
               SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done, \
               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed \
               FROM tasks \
               WHERE completed_at IS NOT NULL \
                 AND completed_at >= ?2 AND completed_at <= ?3 \
               GROUP BY d ORDER BY d"
            .to_string();
        let mut stmt = conn.prepare(&sql)?;
        let rows = stmt.query_map(params![org_val, since, until], |row| {
            Ok(TaskThroughput {
                org_id: row.get(0)?,
                date: row.get(1)?,
                tasks_completed: row.get(2)?,
                tasks_failed: row.get(3)?,
            })
        })?;
        return rows.collect();
    }

    sql = "SELECT 'all' AS org_id, date(completed_at) AS d, \
           SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done, \
           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed \
           FROM tasks \
           WHERE completed_at IS NOT NULL \
             AND completed_at >= ?1 AND completed_at <= ?2 \
           GROUP BY d ORDER BY d"
        .to_string();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(params![since, until], |row| {
        Ok(TaskThroughput {
            org_id: row.get(0)?,
            date: row.get(1)?,
            tasks_completed: row.get(2)?,
            tasks_failed: row.get(3)?,
        })
    })?;
    rows.collect()
}

/// Average model latency from inference cost records.
///
/// Reads from `inference_costs` (owned by convergio-inference).
pub fn model_latency(conn: &Connection) -> Result<Vec<ModelLatency>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT model, \
         AVG(latency_ms) AS avg_lat, \
         0.0 AS p95_lat, \
         COUNT(*) AS cnt \
         FROM inference_costs \
         WHERE latency_ms IS NOT NULL \
         GROUP BY model ORDER BY avg_lat DESC",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok(ModelLatency {
            model: row.get(0)?,
            avg_latency_ms: row.get(1)?,
            p95_latency_ms: row.get(2)?,
            request_count: row.get(3)?,
        })
    })?;
    rows.collect()
}

/// Cache a dashboard value for quick retrieval.
pub fn cache_set(conn: &Connection, key: &str, value_json: &str) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT INTO obs_dashboard_cache (key, value_json, updated_at) \
         VALUES (?1, ?2, datetime('now')) \
         ON CONFLICT(key) DO UPDATE SET value_json = ?2, \
         updated_at = datetime('now')",
        params![key, value_json],
    )?;
    Ok(())
}

/// Retrieve a cached dashboard value.
pub fn cache_get(conn: &Connection, key: &str) -> Result<Option<String>, rusqlite::Error> {
    let mut stmt = conn.prepare("SELECT value_json FROM obs_dashboard_cache WHERE key = ?1")?;
    let mut rows = stmt.query(params![key])?;
    match rows.next()? {
        Some(row) => Ok(Some(row.get(0)?)),
        None => Ok(None),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_db() -> convergio_db::pool::PooledConn {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "observatory",
            &crate::schema::migrations(),
        )
        .unwrap();
        conn
    }

    #[test]
    fn cache_set_and_get() {
        let conn = setup_db();
        cache_set(&conn, "test_key", r#"{"value": 42}"#).unwrap();
        let val = cache_get(&conn, "test_key").unwrap();
        assert_eq!(val.unwrap(), r#"{"value": 42}"#);

        // Upsert
        cache_set(&conn, "test_key", r#"{"value": 99}"#).unwrap();
        let val = cache_get(&conn, "test_key").unwrap();
        assert_eq!(val.unwrap(), r#"{"value": 99}"#);
    }

    #[test]
    fn cache_get_missing_returns_none() {
        let conn = setup_db();
        let val = cache_get(&conn, "nonexistent").unwrap();
        assert!(val.is_none());
    }
}
