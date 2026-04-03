//! Anomaly detection — cost spikes, throughput drops, idle agents.
//!
//! Uses simple statistical thresholds (Z-score style) against recent
//! historical averages. Detected anomalies are persisted for dashboard
//! display and optional webhook notification.

use rusqlite::{params, Connection};

use crate::types::{Anomaly, AnomalyKind, Severity};

/// Record a detected anomaly.
pub fn record_anomaly(
    conn: &Connection,
    kind: &AnomalyKind,
    severity: &Severity,
    entity_id: &str,
    description: &str,
) -> Result<i64, rusqlite::Error> {
    conn.execute(
        "INSERT INTO obs_anomalies (kind, severity, entity_id, description) \
         VALUES (?1, ?2, ?3, ?4)",
        params![
            kind.to_string(),
            severity.to_string(),
            entity_id,
            description,
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// List recent anomalies, optionally filtered by kind.
pub fn list_anomalies(
    conn: &Connection,
    kind: Option<&AnomalyKind>,
    include_resolved: bool,
    limit: u32,
) -> Result<Vec<Anomaly>, rusqlite::Error> {
    let limit = limit.min(200);
    let mut sql = String::from(
        "SELECT id, kind, severity, entity_id, description, detected_at, resolved \
         FROM obs_anomalies WHERE 1=1",
    );
    let mut bind_values: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    let mut idx = 1u32;

    if let Some(k) = kind {
        sql.push_str(&format!(" AND kind = ?{idx}"));
        bind_values.push(Box::new(k.to_string()));
        idx += 1;
    }
    if !include_resolved {
        sql.push_str(" AND resolved = 0");
    }
    let _ = idx;
    sql.push_str(&format!(" ORDER BY detected_at DESC LIMIT {limit}"));

    let refs: Vec<&dyn rusqlite::types::ToSql> = bind_values.iter().map(|b| &**b).collect();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(refs.as_slice(), parse_anomaly_row)?;
    rows.collect()
}

/// Mark an anomaly as resolved.
pub fn resolve_anomaly(conn: &Connection, anomaly_id: i64) -> Result<bool, rusqlite::Error> {
    let updated = conn.execute(
        "UPDATE obs_anomalies SET resolved = 1 WHERE id = ?1",
        params![anomaly_id],
    )?;
    Ok(updated > 0)
}

/// Detect cost spikes: if current hour cost > 3x average of last 24 hours.
///
/// Reads from `billing_usage` (owned by convergio-billing).
pub fn detect_cost_spikes(
    conn: &Connection,
    threshold_multiplier: f64,
) -> Result<Vec<(String, f64, f64)>, rusqlite::Error> {
    // Returns (org_id, current_hour_cost, avg_hourly_cost)
    let mut stmt = conn.prepare(
        "SELECT b.org_id, b.current_cost, a.avg_cost \
         FROM ( \
           SELECT org_id, SUM(cost_usd) AS current_cost \
           FROM billing_usage \
           WHERE created_at >= datetime('now', '-1 hour') \
           GROUP BY org_id \
         ) b \
         JOIN ( \
           SELECT org_id, AVG(hourly_cost) AS avg_cost FROM ( \
             SELECT org_id, strftime('%Y-%m-%dT%H', created_at) AS hr, \
                    SUM(cost_usd) AS hourly_cost \
             FROM billing_usage \
             WHERE created_at >= datetime('now', '-24 hours') \
                AND created_at < datetime('now', '-1 hour') \
             GROUP BY org_id, hr \
           ) GROUP BY org_id \
         ) a ON b.org_id = a.org_id \
         WHERE a.avg_cost > 0 AND b.current_cost > a.avg_cost * ?1",
    )?;
    let rows = stmt.query_map(params![threshold_multiplier], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?))
    })?;
    rows.collect()
}

/// Detect idle agents: agents with heartbeats but no task completions
/// in the last N hours.
///
/// Reads from `ar_agents` and `tasks` (owned by other crates).
pub fn detect_idle_agents(
    conn: &Connection,
    idle_hours: u32,
) -> Result<Vec<(String, String)>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT a.agent_id, a.org_id FROM ar_agents a \
         WHERE a.status = 'active' \
           AND NOT EXISTS ( \
             SELECT 1 FROM tasks t \
             WHERE t.executor_agent = a.agent_id \
               AND t.completed_at >= datetime('now', ?1) \
           )",
    )?;
    let interval = format!("-{idle_hours} hours");
    let rows = stmt.query_map(params![interval], |row| Ok((row.get(0)?, row.get(1)?)))?;
    rows.collect()
}

fn parse_anomaly_row(row: &rusqlite::Row<'_>) -> Result<Anomaly, rusqlite::Error> {
    Ok(Anomaly {
        id: row.get(0)?,
        kind: AnomalyKind::from_str_value(&row.get::<_, String>(1)?),
        severity: Severity::from_str_value(&row.get::<_, String>(2)?),
        entity_id: row.get(3)?,
        description: row.get(4)?,
        detected_at: row.get(5)?,
        resolved: row.get::<_, i32>(6)? != 0,
    })
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
    fn record_and_list_anomalies() {
        let conn = setup_db();
        record_anomaly(
            &conn,
            &AnomalyKind::CostSpike,
            &Severity::High,
            "legal-corp",
            "Cost 5x above average",
        )
        .unwrap();
        record_anomaly(
            &conn,
            &AnomalyKind::IdleAgent,
            &Severity::Low,
            "baccio",
            "No tasks completed in 6 hours",
        )
        .unwrap();

        let all = list_anomalies(&conn, None, false, 100).unwrap();
        assert_eq!(all.len(), 2);

        let spikes = list_anomalies(&conn, Some(&AnomalyKind::CostSpike), false, 100).unwrap();
        assert_eq!(spikes.len(), 1);
        assert_eq!(spikes[0].entity_id, "legal-corp");
    }

    #[test]
    fn resolve_anomaly_works() {
        let conn = setup_db();
        let id = record_anomaly(
            &conn,
            &AnomalyKind::ThroughputDrop,
            &Severity::Medium,
            "dev-corp",
            "Throughput dropped 80%",
        )
        .unwrap();

        assert!(resolve_anomaly(&conn, id).unwrap());

        let unresolved = list_anomalies(&conn, None, false, 100).unwrap();
        assert_eq!(unresolved.len(), 0);

        let all = list_anomalies(&conn, None, true, 100).unwrap();
        assert_eq!(all.len(), 1);
        assert!(all[0].resolved);
    }
}
