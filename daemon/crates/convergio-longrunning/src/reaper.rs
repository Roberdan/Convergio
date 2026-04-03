//! Heartbeat reaper — kills stale long-running executions.
//!
//! Runs periodically, finds executions with no heartbeat beyond 3x interval,
//! marks them as reaped, and propagates death to delegation children.

use std::time::Duration;

use convergio_db::pool::ConnPool;
use rusqlite::params;

use crate::types::LongRunResult;

/// Reap result for a single execution.
#[derive(Debug, Clone)]
pub struct ReapedExecution {
    pub execution_id: String,
    pub elapsed_secs: u64,
    pub max_secs: u64,
}

/// Run one reaper cycle: find stale heartbeats, mark as reaped, kill children.
pub fn reap_cycle(pool: &ConnPool) -> LongRunResult<Vec<ReapedExecution>> {
    let conn = pool.get()?;
    let stale = crate::heartbeat::find_stale(&conn)?;
    let mut reaped = Vec::new();

    for (exec_id, elapsed, max) in &stale {
        tracing::warn!(
            execution_id = exec_id.as_str(),
            elapsed_secs = elapsed,
            max_secs = max,
            "reaping stale execution"
        );
        // Mark execution as reaped
        conn.execute(
            "UPDATE lr_executions SET stage = 'reaped', \
             updated_at = datetime('now') WHERE id = ?1",
            params![exec_id],
        )?;
        // Propagate death to children
        conn.execute(
            "UPDATE lr_executions SET stage = 'reaped', \
             updated_at = datetime('now') \
             WHERE parent_id = ?1 AND stage NOT IN ('completing', 'failed', 'reaped')",
            params![exec_id],
        )?;
        // Clean up heartbeat
        crate::heartbeat::unregister(&conn, exec_id)?;

        reaped.push(ReapedExecution {
            execution_id: exec_id.clone(),
            elapsed_secs: *elapsed,
            max_secs: *max,
        });
    }

    if !reaped.is_empty() {
        tracing::info!(count = reaped.len(), "reaper cycle: reaped executions");
    }
    Ok(reaped)
}

/// Spawn the reaper as a background tokio task.
pub fn spawn_reaper(pool: ConnPool, interval: Duration) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        let mut ticker = tokio::time::interval(interval);
        ticker.tick().await; // skip immediate first tick
        loop {
            ticker.tick().await;
            match reap_cycle(&pool) {
                Ok(reaped) => {
                    if !reaped.is_empty() {
                        tracing::info!(count = reaped.len(), "longrunning reaper: cycle complete");
                    }
                }
                Err(e) => {
                    tracing::warn!("longrunning reaper: cycle failed: {e}");
                }
            }
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reap_cycle_empty_when_no_stale() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        {
            let conn = pool.get().unwrap();
            for m in crate::schema::migrations() {
                conn.execute_batch(m.up).unwrap();
            }
        }
        let reaped = reap_cycle(&pool).unwrap();
        assert!(reaped.is_empty());
    }

    #[test]
    fn reap_cycle_marks_stale_as_reaped() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        {
            let conn = pool.get().unwrap();
            for m in crate::schema::migrations() {
                conn.execute_batch(m.up).unwrap();
            }
            conn.execute(
                "INSERT INTO lr_executions (id, agent, node, stage) \
                 VALUES ('stale-1', 'agent-a', 'node-1', 'running')",
                [],
            )
            .unwrap();
            conn.execute(
                "INSERT INTO lr_heartbeats (execution_id, last_seen, interval_s) \
                 VALUES ('stale-1', datetime('now', '-300 seconds'), 10)",
                [],
            )
            .unwrap();
        }
        let reaped = reap_cycle(&pool).unwrap();
        assert_eq!(reaped.len(), 1);
        assert_eq!(reaped[0].execution_id, "stale-1");

        let conn = pool.get().unwrap();
        let stage: String = conn
            .query_row(
                "SELECT stage FROM lr_executions WHERE id = 'stale-1'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(stage, "reaped");
    }
}
