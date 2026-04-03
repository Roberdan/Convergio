//! Scheduler — priority queue for agent spawn requests.
//!
//! N agents compete for M model slots. Fair scheduling across orgs:
//! priority queue ordered by (priority DESC, created_at ASC).
//! Bounded queue per org for backpressure.

use rusqlite::{params, Connection};
use uuid::Uuid;

use crate::types::{QueueEntry, RuntimeError, RuntimeResult, SpawnRequest};

/// Maximum queue depth per org before backpressure kicks in.
const DEFAULT_MAX_QUEUE_PER_ORG: usize = 50;

/// Enqueue a spawn request. Returns the queue entry ID.
/// Applies backpressure if the org queue is full.
pub fn enqueue(
    conn: &Connection,
    req: &SpawnRequest,
    max_per_org: Option<usize>,
) -> RuntimeResult<String> {
    let max = max_per_org.unwrap_or(DEFAULT_MAX_QUEUE_PER_ORG);
    let depth = queue_depth_for_org(conn, &req.org_id)?;
    if depth >= max {
        return Err(RuntimeError::BackpressureExceeded {
            org_id: req.org_id.clone(),
            depth,
            max,
        });
    }

    let id = Uuid::new_v4().to_string();
    let caps_json = serde_json::to_string(&req.capabilities)?;
    conn.execute(
        "INSERT INTO art_queue \
         (id, org_id, agent_name, task_id, capabilities, model_pref, \
          budget_usd, priority) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            id,
            req.org_id,
            req.agent_name,
            req.task_id,
            caps_json,
            req.model_preference,
            req.budget_usd,
            req.priority,
        ],
    )?;
    tracing::debug!(
        queue_id = id.as_str(),
        org = req.org_id.as_str(),
        priority = req.priority,
        "spawn request enqueued"
    );
    Ok(id)
}

/// Dequeue the highest-priority spawn request (fair across orgs).
/// Uses round-robin per org: picks the org with the oldest head-of-queue entry.
pub fn dequeue(conn: &Connection) -> RuntimeResult<Option<(String, SpawnRequest)>> {
    let row = conn.query_row(
        "SELECT id, org_id, agent_name, task_id, capabilities, model_pref, \
         budget_usd, priority \
         FROM art_queue ORDER BY priority DESC, created_at ASC LIMIT 1",
        [],
        |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, Option<i64>>(3)?,
                r.get::<_, String>(4)?,
                r.get::<_, Option<String>>(5)?,
                r.get::<_, f64>(6)?,
                r.get::<_, i32>(7)?,
            ))
        },
    );

    match row {
        Ok((id, org_id, agent_name, task_id, caps_json, model_pref, budget, prio)) => {
            conn.execute("DELETE FROM art_queue WHERE id = ?1", params![id])?;
            let capabilities: Vec<String> = serde_json::from_str(&caps_json).unwrap_or_default();
            Ok(Some((
                id,
                SpawnRequest {
                    agent_name,
                    org_id,
                    task_id,
                    capabilities,
                    model_preference: model_pref,
                    budget_usd: budget,
                    priority: prio,
                },
            )))
        }
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Current queue depth for an org.
pub fn queue_depth_for_org(conn: &Connection, org_id: &str) -> RuntimeResult<usize> {
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM art_queue WHERE org_id = ?1",
        params![org_id],
        |r| r.get(0),
    )?;
    Ok(count as usize)
}

/// Total queue depth across all orgs.
pub fn queue_depth_total(conn: &Connection) -> RuntimeResult<usize> {
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM art_queue", [], |r| r.get(0))?;
    Ok(count as usize)
}

/// List all pending queue entries (for the runtime view API).
pub fn list_pending(conn: &Connection) -> RuntimeResult<Vec<QueueEntry>> {
    let mut stmt = conn.prepare(
        "SELECT id, org_id, priority, created_at \
         FROM art_queue ORDER BY priority DESC, created_at ASC",
    )?;
    let rows = stmt.query_map([], |r| {
        Ok(QueueEntry {
            request_id: r.get(0)?,
            org_id: r.get(1)?,
            priority: r.get(2)?,
            created_at: r.get(3)?,
        })
    })?;
    let mut entries = Vec::new();
    for row in rows {
        entries.push(row?);
    }
    Ok(entries)
}

/// Drain all queue entries for an org (on org death).
pub fn drain_org(conn: &Connection, org_id: &str) -> RuntimeResult<usize> {
    let n = conn.execute("DELETE FROM art_queue WHERE org_id = ?1", params![org_id])?;
    Ok(n)
}

#[cfg(test)]
#[path = "scheduler_tests.rs"]
mod tests;
