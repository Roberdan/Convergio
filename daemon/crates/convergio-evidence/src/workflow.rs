// Workflow automation — Thor auto-trigger, stale task reaper with notifications.
// WHY: operational lessons become code, not just docs.

use convergio_db::pool::ConnPool;
use rusqlite::{params, Connection};

/// Check if a wave is complete (all tasks done/skipped/cancelled).
/// If so, auto-enqueue Thor validation for the wave.
pub fn check_wave_completion(conn: &Connection, wave_id: i64) -> Result<bool, String> {
    let (total, completed): (i64, i64) = conn
        .query_row(
            "SELECT COUNT(*), \
             SUM(CASE WHEN status IN ('done','skipped','cancelled') THEN 1 ELSE 0 END) \
             FROM tasks WHERE wave_id = ?1",
            params![wave_id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .map_err(|e| format!("wave completion check failed: {e}"))?;

    if total == 0 || completed < total {
        return Ok(false);
    }

    // Update wave status
    conn.execute(
        "UPDATE waves SET status='completed' WHERE id=?1 AND status != 'completed'",
        params![wave_id],
    )
    .map_err(|e| format!("wave status update failed: {e}"))?;

    // Auto-enqueue Thor validation for the wave's plan
    let plan_id: i64 = conn
        .query_row(
            "SELECT plan_id FROM waves WHERE id = ?1",
            params![wave_id],
            |r| r.get(0),
        )
        .map_err(|e| format!("wave lookup failed: {e}"))?;

    // Enqueue validation (idempotent)
    conn.execute(
        "INSERT OR IGNORE INTO validation_queue (wave_id, plan_id) VALUES (?1, ?2)",
        params![wave_id, plan_id],
    )
    .map_err(|e| format!("enqueue validation failed: {e}"))?;

    tracing::info!("workflow: wave {wave_id} complete, Thor validation enqueued");
    Ok(true)
}

/// Detect stale tasks: in_progress for longer than threshold.
/// Records notifications so we don't spam.
pub fn detect_stale_tasks(
    conn: &Connection,
    max_age_minutes: i64,
) -> Result<Vec<(i64, String)>, String> {
    let interval = format!("-{max_age_minutes} minutes");
    let mut stmt = conn
        .prepare(
            "SELECT t.id, t.title FROM tasks t \
             WHERE t.status = 'in_progress' \
             AND t.started_at < datetime('now', ?1) \
             AND t.id NOT IN (SELECT task_id FROM stale_task_notifications \
                              WHERE resolved = 0)",
        )
        .map_err(|e| format!("stale query failed: {e}"))?;

    let stale: Vec<(i64, String)> = stmt
        .query_map(params![interval], |r| Ok((r.get(0)?, r.get(1)?)))
        .map_err(|e| format!("stale query exec failed: {e}"))?
        .filter_map(|r| r.ok())
        .collect();

    // Record notifications for newly detected stale tasks
    for (task_id, _) in &stale {
        conn.execute(
            "INSERT OR IGNORE INTO stale_task_notifications (task_id, reason) \
             VALUES (?1, 'stale_in_progress')",
            params![task_id],
        )
        .ok();
    }

    if !stale.is_empty() {
        tracing::warn!("workflow: detected {} stale in_progress tasks", stale.len());
    }

    Ok(stale)
}

/// Resolve stale notifications when a task progresses.
pub fn resolve_stale_notification(conn: &Connection, task_id: i64) {
    conn.execute(
        "UPDATE stale_task_notifications SET resolved = 1 WHERE task_id = ?1",
        params![task_id],
    )
    .ok();
}

/// Match a commit hash to a task by scanning task_id or title in the message.
/// Convention: commit message contains "task-<id>" or "#<id>".
pub fn match_commit_to_task(
    conn: &Connection,
    commit_hash: &str,
    commit_message: &str,
) -> Vec<i64> {
    let mut matched = Vec::new();

    // Extract task references: "task-123", "#123"
    for word in commit_message.split_whitespace() {
        let id = if let Some(rest) = word.strip_prefix("task-") {
            rest.parse::<i64>().ok()
        } else if let Some(rest) = word.strip_prefix('#') {
            rest.parse::<i64>().ok()
        } else {
            None
        };

        if let Some(task_id) = id {
            // Verify task exists
            let exists: i64 = conn
                .query_row(
                    "SELECT COUNT(*) FROM tasks WHERE id = ?1",
                    params![task_id],
                    |r| r.get(0),
                )
                .unwrap_or(0);
            if exists > 0 {
                crate::evidence::record_commit_match(conn, task_id, commit_hash, commit_message)
                    .ok();
                // Also record as commit_hash evidence
                crate::evidence::record_evidence(
                    conn,
                    task_id,
                    "commit_hash",
                    commit_hash,
                    commit_message,
                    0,
                )
                .ok();
                matched.push(task_id);
            }
        }
    }
    matched
}

/// Spawn background workflow monitor (stale detection every 5 min).
pub fn spawn_workflow_monitor(pool: ConnPool) {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(300));
        loop {
            interval.tick().await;
            let conn = match pool.get() {
                Ok(c) => c,
                Err(e) => {
                    tracing::warn!("workflow_monitor: pool error: {e}");
                    continue;
                }
            };
            // Detect stale tasks (>60 min in_progress)
            if let Err(e) = detect_stale_tasks(&conn, 60) {
                tracing::warn!("workflow_monitor: stale detection failed: {e}");
            }
            // Check all active waves for completion
            check_active_waves(&conn);
        }
    });
}

/// Scan all active waves and trigger completion flow if done.
fn check_active_waves(conn: &Connection) {
    let wave_ids: Vec<i64> = conn
        .prepare("SELECT id FROM waves WHERE status IN ('active', 'pending')")
        .and_then(|mut s| {
            s.query_map([], |r| r.get(0))
                .map(|rows| rows.filter_map(|r| r.ok()).collect())
        })
        .unwrap_or_default();

    for wave_id in wave_ids {
        if let Err(e) = check_wave_completion(conn, wave_id) {
            tracing::debug!("workflow_monitor: wave {wave_id}: {e}");
        }
    }
}

#[cfg(test)]
#[path = "workflow_tests.rs"]
mod tests;
