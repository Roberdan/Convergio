//! Progress tracking and SSE streaming for long-running executions.
//!
//! Updates are stored in lr_executions and published to the IPC event bus
//! so SSE clients can stream percentage, stage, cost, and ETA in real time.

use std::sync::Arc;

use convergio_ipc::sse::{EventBus, IpcEvent};
use rusqlite::{params, Connection};

use crate::types::{ExecutionStage, LongRunResult, ProgressSnapshot};

/// Update progress for an execution and publish via SSE.
pub fn update(
    conn: &Connection,
    bus: Option<&Arc<EventBus>>,
    snap: &ProgressSnapshot,
) -> LongRunResult<()> {
    conn.execute(
        "UPDATE lr_executions SET percent = ?1, stage = ?2, \
         message = ?3, updated_at = datetime('now') WHERE id = ?4",
        params![
            snap.percent,
            snap.stage.as_str(),
            snap.message,
            snap.execution_id,
        ],
    )?;

    // Publish to SSE bus if available
    if let Some(bus) = bus {
        let data = serde_json::to_string(snap).unwrap_or_default();
        bus.publish(IpcEvent {
            from: "longrunning".into(),
            to: None,
            content: data,
            event_type: "progress".into(),
            ts: chrono::Utc::now().to_rfc3339(),
        });
    }

    Ok(())
}

/// Load current progress for an execution.
pub fn load(conn: &Connection, execution_id: &str) -> LongRunResult<Option<ProgressSnapshot>> {
    let result = conn.query_row(
        "SELECT percent, stage, spent_usd, message FROM lr_executions \
         WHERE id = ?1",
        params![execution_id],
        |row| {
            Ok((
                row.get::<_, f64>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, f64>(2)?,
                row.get::<_, Option<String>>(3)?,
            ))
        },
    );
    match result {
        Ok((percent, stage_str, cost, message)) => {
            let stage = ExecutionStage::parse(&stage_str).unwrap_or(ExecutionStage::Running);
            Ok(Some(ProgressSnapshot {
                execution_id: execution_id.to_string(),
                percent,
                stage,
                cost_usd: cost,
                eta_secs: None,
                message,
            }))
        }
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute(
            "INSERT INTO lr_executions (id, agent, node) \
             VALUES ('e1', 'agent-a', 'node-1')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn update_and_load_progress() {
        let conn = setup();
        let snap = ProgressSnapshot {
            execution_id: "e1".into(),
            percent: 55.0,
            stage: ExecutionStage::Running,
            cost_usd: 0.12,
            eta_secs: Some(60),
            message: Some("wave 3 of 5".into()),
        };
        update(&conn, None, &snap).unwrap();
        let loaded = load(&conn, "e1").unwrap().unwrap();
        assert!((loaded.percent - 55.0).abs() < 0.001);
        assert_eq!(loaded.stage, ExecutionStage::Running);
        assert_eq!(loaded.message.as_deref(), Some("wave 3 of 5"));
    }

    #[test]
    fn load_missing_returns_none() {
        let conn = setup();
        assert!(load(&conn, "nonexistent").unwrap().is_none());
    }

    #[test]
    fn update_with_event_bus() {
        let bus = Arc::new(EventBus::new(16));
        let mut rx = bus.subscribe();
        let conn = setup();
        let snap = ProgressSnapshot {
            execution_id: "e1".into(),
            percent: 75.0,
            stage: ExecutionStage::Checkpointing,
            cost_usd: 0.0,
            eta_secs: None,
            message: None,
        };
        update(&conn, Some(&bus), &snap).unwrap();
        let event = rx.try_recv().unwrap();
        assert_eq!(event.event_type, "progress");
        assert!(event.content.contains("75.0"));
    }
}
