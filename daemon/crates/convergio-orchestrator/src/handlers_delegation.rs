// Handlers for wave execution and delegation.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use rusqlite::params;

use crate::actions;

type AliResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

pub async fn on_wave_ready(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    wave_id: i64,
    plan_id: i64,
) -> AliResult {
    let conn = pool.get()?;

    conn.execute(
        "UPDATE waves SET status='in_progress', started_at=datetime('now') WHERE id=?1",
        params![wave_id],
    )?;

    let task_count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM tasks WHERE plan_id=?1 AND wave_id=?2 AND status='pending'",
        params![plan_id, wave_id],
        |r| r.get(0),
    )?;

    tracing::info!(
        "ali: wave {wave_id} starting with {task_count} pending tasks for plan {plan_id}"
    );
    actions::delegate_plan(pool, notify, plan_id).await
}

pub async fn on_delegation_failed(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    plan_id: i64,
    failed_peer: &str,
    reason: &str,
) -> AliResult {
    tracing::warn!("ali: delegation of plan {plan_id} to {failed_peer} failed: {reason}");

    let alt_peer = actions::find_available_peer(Some(failed_peer)).await;

    if let Some(peer) = alt_peer {
        tracing::info!("ali: retrying plan {plan_id} on peer {peer}");
        crate::executor::delegate_to_peer(pool, notify, plan_id, &peer).await
    } else {
        tracing::warn!("ali: no peers available for plan {plan_id}, requesting human");
        actions::emit(
            pool,
            notify,
            "need_human",
            &serde_json::json!({
                "plan_id": plan_id,
                "reason": format!("delegation failed on {failed_peer}: {reason}, no alternative peers"),
            }),
        )
    }
}
