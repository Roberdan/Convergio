//! Export — Prometheus/Grafana metrics and webhook event delivery.

use rusqlite::{params, Connection};

use crate::types::{PrometheusMetric, WebhookPayload};

/// Generate Prometheus-compatible text exposition from observatory data.
pub fn prometheus_exposition(conn: &Connection) -> Result<String, rusqlite::Error> {
    let metrics = collect_prometheus_metrics(conn)?;
    let mut out = String::new();
    for m in &metrics {
        out.push_str(&format!("# HELP {} {}\n", m.name, m.help));
        out.push_str(&format!("# TYPE {} {}\n", m.name, m.metric_type));
        if m.labels.is_empty() {
            out.push_str(&format!("{} {}\n", m.name, m.value));
        } else {
            let labels: Vec<String> = m
                .labels
                .iter()
                .map(|(k, v)| format!("{k}=\"{v}\""))
                .collect();
            out.push_str(&format!("{}{{{}}} {}\n", m.name, labels.join(","), m.value));
        }
    }
    Ok(out)
}

/// Collect raw Prometheus metrics from observatory tables.
pub fn collect_prometheus_metrics(
    conn: &Connection,
) -> Result<Vec<PrometheusMetric>, rusqlite::Error> {
    let mut metrics = Vec::new();

    // Total timeline events
    if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM obs_timeline", [], |r| {
        r.get::<_, f64>(0)
    }) {
        metrics.push(PrometheusMetric {
            name: "convergio_timeline_events_total".into(),
            help: "Total timeline events recorded".into(),
            metric_type: "counter".into(),
            value: n,
            labels: vec![],
        });
    }

    // Unresolved anomalies
    if let Ok(n) = conn.query_row(
        "SELECT COUNT(*) FROM obs_anomalies WHERE resolved = 0",
        [],
        |r| r.get::<_, f64>(0),
    ) {
        metrics.push(PrometheusMetric {
            name: "convergio_anomalies_unresolved".into(),
            help: "Number of unresolved anomalies".into(),
            metric_type: "gauge".into(),
            value: n,
            labels: vec![],
        });
    }

    // Events by source (last 24h)
    let mut stmt = conn.prepare(
        "SELECT source, COUNT(*) FROM obs_timeline \
         WHERE created_at >= datetime('now', '-24 hours') \
         GROUP BY source",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok((row.get::<_, String>(0)?, row.get::<_, f64>(1)?))
    })?;
    for r in rows {
        let (source, count) = r?;
        metrics.push(PrometheusMetric {
            name: "convergio_timeline_events_24h".into(),
            help: "Timeline events in last 24h by source".into(),
            metric_type: "gauge".into(),
            value: count,
            labels: vec![("source".into(), source)],
        });
    }

    Ok(metrics)
}

/// Register a webhook endpoint.
pub fn register_webhook(
    conn: &Connection,
    url: &str,
    event_filter: &str,
) -> Result<i64, rusqlite::Error> {
    conn.execute(
        "INSERT INTO obs_webhooks (url, event_filter) VALUES (?1, ?2)",
        params![url, event_filter],
    )?;
    Ok(conn.last_insert_rowid())
}

/// List active webhooks.
pub fn list_webhooks(conn: &Connection) -> Result<Vec<(i64, String, String)>, rusqlite::Error> {
    let mut stmt =
        conn.prepare("SELECT id, url, event_filter FROM obs_webhooks WHERE active = 1")?;
    let rows = stmt.query_map([], |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)))?;
    rows.collect()
}

/// Remove a webhook.
pub fn remove_webhook(conn: &Connection, webhook_id: i64) -> Result<bool, rusqlite::Error> {
    let n = conn.execute(
        "UPDATE obs_webhooks SET active = 0 WHERE id = ?1",
        params![webhook_id],
    )?;
    Ok(n > 0)
}

/// Build a webhook payload for an event.
pub fn build_payload(event_type: &str, data: serde_json::Value) -> WebhookPayload {
    WebhookPayload {
        event_type: event_type.to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        data,
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
    fn prometheus_exposition_format() {
        let conn = setup_db();
        // Insert some timeline events
        conn.execute(
            "INSERT INTO obs_timeline (source, event_type, actor, summary) \
             VALUES ('system', 'boot', 'daemon', 'Started')",
            [],
        )
        .unwrap();
        let text = prometheus_exposition(&conn).unwrap();
        assert!(text.contains("convergio_timeline_events_total"));
        assert!(text.contains("# HELP"));
        assert!(text.contains("# TYPE"));
    }

    #[test]
    fn webhook_crud() {
        let conn = setup_db();
        let id = register_webhook(&conn, "https://example.com/webhook", "anomaly.*").unwrap();
        assert!(id > 0);

        let hooks = list_webhooks(&conn).unwrap();
        assert_eq!(hooks.len(), 1);
        assert_eq!(hooks[0].1, "https://example.com/webhook");

        assert!(remove_webhook(&conn, id).unwrap());
        let hooks = list_webhooks(&conn).unwrap();
        assert_eq!(hooks.len(), 0);
    }

    #[test]
    fn build_payload_populates_fields() {
        let p = build_payload(
            "anomaly.cost_spike",
            serde_json::json!({"org": "legal-corp"}),
        );
        assert_eq!(p.event_type, "anomaly.cost_spike");
        assert!(!p.timestamp.is_empty());
    }
}
