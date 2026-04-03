//! GC/Reaper — collects dead agents, orphan tasks, expired delegations, budget leaks.
//!
//! Runs periodically + on-demand. Reaps stale heartbeats, auto-returns expired
//! delegations, cleans up scope rules and workspaces.

use std::time::Duration;

use convergio_db::pool::ConnPool;
use rusqlite::params;

use crate::types::RuntimeResult;

/// Result of a single reaper cycle.
#[derive(Debug, Clone, Default)]
pub struct ReaperReport {
    pub stale_agents_reaped: usize,
    pub expired_delegations_returned: usize,
    pub orphan_scopes_cleaned: usize,
}

/// Run one reaper cycle.
pub fn reap_cycle(pool: &ConnPool) -> RuntimeResult<ReaperReport> {
    let conn = pool.get()?;
    let mut report = ReaperReport::default();

    // 1. Reap stale heartbeats
    let stale = crate::heartbeat::find_stale(&conn)?;
    for (agent_id, elapsed, max) in &stale {
        tracing::warn!(
            agent_id = agent_id.as_str(),
            elapsed,
            max,
            "reaping stale agent"
        );
        conn.execute(
            "UPDATE art_agents SET stage = 'reaped', updated_at = datetime('now') \
             WHERE id = ?1 AND stage NOT IN ('stopped', 'reaped')",
            params![agent_id],
        )?;
        crate::heartbeat::unregister(&conn, agent_id)?;
        report.stale_agents_reaped += 1;
    }

    // 2. Auto-return expired delegations
    let expired = crate::delegation::find_expired(&conn)?;
    for deleg in &expired {
        tracing::warn!(
            delegation_id = deleg.id.as_str(),
            agent_id = deleg.agent_id.as_str(),
            "auto-returning expired delegation"
        );
        crate::delegation::return_agent(&conn, &deleg.id)?;
        report.expired_delegations_returned += 1;
    }

    // 3. Clean scope rules for reaped/stopped agents
    let cleaned = conn.execute(
        "DELETE FROM art_scope_rules WHERE agent_id IN \
         (SELECT id FROM art_agents WHERE stage IN ('reaped', 'stopped'))",
        [],
    )?;
    report.orphan_scopes_cleaned = cleaned;

    if report.stale_agents_reaped > 0
        || report.expired_delegations_returned > 0
        || report.orphan_scopes_cleaned > 0
    {
        tracing::info!(
            stale = report.stale_agents_reaped,
            expired = report.expired_delegations_returned,
            scopes = report.orphan_scopes_cleaned,
            "reaper cycle complete"
        );
    }

    Ok(report)
}

/// Spawn the reaper as a background tokio task.
pub fn spawn_reaper(pool: ConnPool, interval: Duration) -> tokio::task::JoinHandle<()> {
    tokio::spawn(async move {
        let mut ticker = tokio::time::interval(interval);
        ticker.tick().await; // skip immediate first tick
        loop {
            ticker.tick().await;
            match reap_cycle(&pool) {
                Ok(_) => {}
                Err(e) => {
                    tracing::warn!("agent-runtime reaper: cycle failed: {e}");
                }
            }
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reap_cycle_empty_when_nothing_stale() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        {
            let conn = pool.get().unwrap();
            for m in crate::schema::migrations() {
                conn.execute_batch(m.up).unwrap();
            }
        }
        let report = reap_cycle(&pool).unwrap();
        assert_eq!(report.stale_agents_reaped, 0);
        assert_eq!(report.expired_delegations_returned, 0);
    }

    #[test]
    fn reap_cycle_reaps_stale_agents() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        {
            let conn = pool.get().unwrap();
            for m in crate::schema::migrations() {
                conn.execute_batch(m.up).unwrap();
            }
            conn.execute(
                "INSERT INTO art_agents (id, agent_name, org_id, node, stage) \
                 VALUES ('stale-1', 'elena', 'legal-corp', 'n1', 'running')",
                [],
            )
            .unwrap();
            conn.execute(
                "INSERT INTO art_heartbeats (agent_id, last_seen, interval_s) \
                 VALUES ('stale-1', datetime('now', '-300 seconds'), 10)",
                [],
            )
            .unwrap();
            // Add a scope rule that should be cleaned
            conn.execute(
                "INSERT INTO art_scope_rules (agent_id, resource, access) \
                 VALUES ('stale-1', '/workspace/file.rs', 'write')",
                [],
            )
            .unwrap();
        }

        let report = reap_cycle(&pool).unwrap();
        assert_eq!(report.stale_agents_reaped, 1);

        let conn = pool.get().unwrap();
        let stage: String = conn
            .query_row(
                "SELECT stage FROM art_agents WHERE id = 'stale-1'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(stage, "reaped");
    }
}
