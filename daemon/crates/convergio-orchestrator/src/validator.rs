// Thor validator service — durable queue + persistent verdicts.

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueEntry {
    pub id: i64,
    pub task_id: Option<i64>,
    pub wave_id: Option<i64>,
    pub plan_id: Option<i64>,
    pub status: String,
    pub created_at: String,
    pub started_at: Option<String>,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Verdict {
    pub id: i64,
    pub queue_id: i64,
    pub verdict: String,
    pub report: Option<String>,
    pub validator: Option<String>,
    pub created_at: String,
}

/// Enqueue a validation request. Idempotent: returns existing entry if pending/running.
pub fn enqueue_validation(
    conn: &Connection,
    task_id: Option<i64>,
    wave_id: Option<i64>,
    plan_id: Option<i64>,
) -> rusqlite::Result<i64> {
    if let Some(tid) = task_id {
        if let Ok(existing) = conn.query_row(
            "SELECT id FROM validation_queue WHERE task_id=?1 AND status IN ('pending','running') LIMIT 1",
            params![tid],
            |r| r.get::<_, i64>(0),
        ) {
            return Ok(existing);
        }
    }
    conn.execute(
        "INSERT INTO validation_queue (task_id, wave_id, plan_id) VALUES (?1, ?2, ?3)",
        params![task_id, wave_id, plan_id],
    )?;
    Ok(conn.last_insert_rowid())
}

pub fn get_pending(conn: &Connection) -> rusqlite::Result<Vec<QueueEntry>> {
    let mut stmt = conn.prepare(
        "SELECT id, task_id, wave_id, plan_id, status, created_at, started_at, completed_at
         FROM validation_queue WHERE status='pending' ORDER BY id",
    )?;
    let rows = stmt.query_map([], |r| {
        Ok(QueueEntry {
            id: r.get(0)?, task_id: r.get(1)?, wave_id: r.get(2)?,
            plan_id: r.get(3)?, status: r.get(4)?, created_at: r.get(5)?,
            started_at: r.get(6)?, completed_at: r.get(7)?,
        })
    })?;
    rows.collect()
}

pub fn list_queue(conn: &Connection) -> rusqlite::Result<Vec<QueueEntry>> {
    let mut stmt = conn.prepare(
        "SELECT id, task_id, wave_id, plan_id, status, created_at, started_at, completed_at
         FROM validation_queue ORDER BY id DESC LIMIT 200",
    )?;
    let rows = stmt.query_map([], |r| {
        Ok(QueueEntry {
            id: r.get(0)?, task_id: r.get(1)?, wave_id: r.get(2)?,
            plan_id: r.get(3)?, status: r.get(4)?, created_at: r.get(5)?,
            started_at: r.get(6)?, completed_at: r.get(7)?,
        })
    })?;
    rows.collect()
}

pub fn record_verdict(
    conn: &Connection,
    queue_id: i64,
    verdict: &str,
    report: Option<&str>,
    validator: Option<&str>,
) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO validation_verdicts (queue_id, verdict, report, validator) VALUES (?1, ?2, ?3, ?4)",
        params![queue_id, verdict, report, validator],
    )?;
    conn.execute(
        "UPDATE validation_queue SET status='completed', completed_at=datetime('now') WHERE id=?1",
        params![queue_id],
    )?;
    Ok(())
}

pub fn get_verdict(conn: &Connection, task_id: i64) -> rusqlite::Result<Option<Verdict>> {
    let result = conn.query_row(
        "SELECT v.id, v.queue_id, v.verdict, v.report, v.validator, v.created_at
         FROM validation_verdicts v
         JOIN validation_queue q ON v.queue_id = q.id
         WHERE q.task_id = ?1 ORDER BY v.id DESC LIMIT 1",
        params![task_id],
        |r| Ok(Verdict {
            id: r.get(0)?, queue_id: r.get(1)?, verdict: r.get(2)?,
            report: r.get(3)?, validator: r.get(4)?, created_at: r.get(5)?,
        }),
    );
    match result {
        Ok(v) => Ok(Some(v)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e),
    }
}

pub fn timeout_stale(conn: &Connection, max_age_secs: u64) -> rusqlite::Result<usize> {
    let interval = format!("-{max_age_secs} seconds");
    let mut stmt = conn.prepare(
        "SELECT id FROM validation_queue WHERE status IN ('pending','running')
         AND created_at < datetime('now', ?1)",
    )?;
    let ids: Vec<i64> = stmt
        .query_map(params![interval], |r| r.get(0))?
        .collect::<rusqlite::Result<Vec<_>>>()?;
    let count = ids.len();
    for id in &ids {
        conn.execute("UPDATE validation_queue SET status='failed', completed_at=datetime('now') WHERE id=?1", params![id])?;
        conn.execute(
            "INSERT INTO validation_verdicts (queue_id, verdict, report, validator) \
             VALUES (?1, 'timeout', 'Timed out waiting for validator', 'system')",
            params![id],
        )?;
    }
    Ok(count)
}

fn entry_verdict(db: &Connection, entry: &QueueEntry) -> &'static str {
    let Some(tid) = entry.task_id else { return "needs_review" };
    match db.query_row("SELECT status FROM tasks WHERE id=?1", params![tid], |r| r.get::<_, String>(0)) {
        Ok(s) if s == "submitted" || s == "done" => "pass",
        Ok(s) => {
            tracing::warn!("validator_loop: task {tid} status '{s}'");
            "needs_review"
        }
        Err(_) => "fail",
    }
}

/// Spawn background task that processes pending validations every 30s.
pub fn spawn_validator_loop(pool: convergio_db::pool::ConnPool) {
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(30)).await;
            let conn = match pool.get() {
                Ok(c) => c,
                Err(e) => { tracing::warn!("validator_loop: pool get failed: {e}"); continue; }
            };
            match timeout_stale(&conn, 600) {
                Ok(n) if n > 0 => tracing::info!("validator_loop: timed out {n} stale entries"),
                Err(e) => tracing::warn!("validator_loop: timeout_stale failed: {e}"),
                _ => {}
            }
            let pending = match get_pending(&conn) {
                Ok(p) => p,
                Err(e) => { tracing::warn!("validator_loop: get_pending failed: {e}"); continue; }
            };
            for entry in &pending {
                conn.execute(
                    "UPDATE validation_queue SET status='running', started_at=datetime('now') WHERE id=?1",
                    params![entry.id],
                ).ok();
                if let Err(e) = record_verdict(&conn, entry.id, entry_verdict(&conn, entry), Some("mechanical gate"), Some("validator-loop")) {
                    tracing::warn!("validator_loop: record_verdict failed: {e}");
                }
            }
            if !pending.is_empty() {
                tracing::info!("validator_loop: processed {} entries", pending.len());
            }
        }
    });
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
    fn enqueue_and_list() {
        let conn = setup();
        let id = enqueue_validation(&conn, Some(1), Some(1), Some(1)).unwrap();
        assert!(id > 0);
        let q = list_queue(&conn).unwrap();
        assert_eq!(q.len(), 1);
        assert_eq!(q[0].status, "pending");
    }

    #[test]
    fn enqueue_idempotent() {
        let conn = setup();
        let id1 = enqueue_validation(&conn, Some(1), None, None).unwrap();
        let id2 = enqueue_validation(&conn, Some(1), None, None).unwrap();
        assert_eq!(id1, id2);
    }

    #[test]
    fn record_verdict_completes_entry() {
        let conn = setup();
        let id = enqueue_validation(&conn, Some(1), None, None).unwrap();
        record_verdict(&conn, id, "pass", Some("ok"), Some("thor")).unwrap();
        let q = list_queue(&conn).unwrap();
        assert_eq!(q[0].status, "completed");
    }

    #[test]
    fn get_verdict_returns_latest() {
        let conn = setup();
        let id = enqueue_validation(&conn, Some(42), None, None).unwrap();
        record_verdict(&conn, id, "pass", None, None).unwrap();
        let v = get_verdict(&conn, 42).unwrap().unwrap();
        assert_eq!(v.verdict, "pass");
    }

    #[test]
    fn get_verdict_none_for_unknown() {
        let conn = setup();
        assert!(get_verdict(&conn, 999).unwrap().is_none());
    }
}
