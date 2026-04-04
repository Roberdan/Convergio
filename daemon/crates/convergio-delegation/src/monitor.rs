//! Remote delegation monitor — polls tmux window on peer, syncs back on exit.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::events::{make_event, DomainEventSink, EventContext, EventKind};
use tokio::task::JoinHandle;

use crate::queries;
use crate::types::{DelegationStatus, DelegationStep, PipelineConfig};

const POLL_INTERVAL_SECS: u64 = 30;

/// Check if a tmux window is still alive on the remote peer via SSH.
async fn is_tmux_window_alive(ssh_target: &str, tmux_session: &str, tmux_window: &str) -> bool {
    let output = tokio::process::Command::new("ssh")
        .args([
            ssh_target,
            "tmux",
            "list-windows",
            "-t",
            tmux_session,
            "-F",
            "#{window_name}",
        ])
        .output()
        .await;
    match output {
        Ok(o) if o.status.success() => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            stdout.lines().any(|line| line.trim() == tmux_window)
        }
        _ => false,
    }
}

/// Spawn a background task that monitors a remote delegation.
///
/// Polls the remote tmux session every 30s. When the window disappears
/// (agent exited), syncs results back and emits a `DelegationCompleted` event.
#[allow(clippy::too_many_arguments)]
pub fn monitor_remote_delegation(
    pool: ConnPool,
    delegation_id: String,
    peer_name: String,
    ssh_target: String,
    tmux_session: String,
    tmux_window: String,
    config: PipelineConfig,
    event_sink: Option<Arc<dyn DomainEventSink>>,
) -> JoinHandle<()> {
    tokio::spawn(async move {
        tracing::info!(
            delegation_id = delegation_id.as_str(),
            peer_name = peer_name.as_str(),
            "monitor started for remote delegation"
        );
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(POLL_INTERVAL_SECS)).await;
            let alive = is_tmux_window_alive(&ssh_target, &tmux_session, &tmux_window).await;
            if alive {
                continue;
            }
            tracing::info!(
                delegation_id = delegation_id.as_str(),
                "remote tmux window gone, starting sync_back"
            );
            break;
        }
        // Agent exited — sync back results
        let result = crate::pipeline::sync_back(&pool, &delegation_id, &peer_name, &config).await;
        match result {
            Ok(()) => {
                tracing::info!(delegation_id = delegation_id.as_str(), "sync_back complete");
                emit_completed(&pool, &delegation_id, &peer_name, &event_sink);
            }
            Err(e) => {
                tracing::error!(
                    delegation_id = delegation_id.as_str(),
                    error = %e,
                    "sync_back failed"
                );
                let fail = DelegationStatus::Failed(format!("sync_back: {e}"));
                let _ = queries::update_delegation_status(
                    &pool,
                    &delegation_id,
                    &fail,
                    &DelegationStep::SyncBack,
                );
            }
        }
    })
}

/// Emit a DelegationCompleted event if we have a sink and can read plan_id.
fn emit_completed(
    pool: &ConnPool,
    delegation_id: &str,
    peer_name: &str,
    event_sink: &Option<Arc<dyn DomainEventSink>>,
) {
    let Some(sink) = event_sink else { return };
    let plan_id = pool
        .get()
        .ok()
        .and_then(|conn| queries::get_delegation(&conn, delegation_id))
        .map(|rec| rec.plan_id)
        .unwrap_or(0);
    let event = make_event(
        "delegation-monitor",
        EventKind::DelegationCompleted {
            delegation_id: delegation_id.to_string(),
            plan_id,
            peer_name: peer_name.to_string(),
        },
        EventContext {
            plan_id: Some(plan_id),
            ..Default::default()
        },
    );
    sink.emit(event);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn tmux_check_builds_correct_command() {
        // On CI/local without SSH, the command will fail — that means "not alive".
        let alive = is_tmux_window_alive("nobody@127.0.0.1", "cvg-test-session", "plan-999").await;
        assert!(!alive, "should be false when ssh fails");
    }

    #[tokio::test]
    async fn monitor_handles_immediate_exit() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute(
            "INSERT INTO delegations (delegation_id,plan_id,peer_name,source_path) \
             VALUES('del-mon-1',1,'test-peer','/tmp')",
            [],
        )
        .unwrap();
        drop(conn);

        // Use a bogus ssh_target so tmux check fails immediately (not alive)
        let handle = monitor_remote_delegation(
            pool.clone(),
            "del-mon-1".into(),
            "test-peer".into(),
            "nobody@127.0.0.1".into(),
            "cvg-del-mon-1".into(),
            "plan-1".into(),
            PipelineConfig::default(),
            None,
        );
        // The monitor will detect "not alive" on first poll, then sync_back
        // will fail (no real peer), marking delegation as failed.
        let _ = tokio::time::timeout(std::time::Duration::from_secs(35), handle).await;

        let conn = pool.get().unwrap();
        let rec = queries::get_delegation(&conn, "del-mon-1").unwrap();
        assert!(
            rec.status.starts_with("failed"),
            "expected failed status, got: {}",
            rec.status
        );
    }
}
