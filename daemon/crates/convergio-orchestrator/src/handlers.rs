// Handlers — one function per orchestration event type.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use rusqlite::params;

use crate::actions;
use crate::plan_hierarchy;

type AliResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

pub async fn on_plan_ready(pool: &ConnPool, notify: &Arc<Notify>, plan_id: i64) -> AliResult {
    let conn = pool.get()?;
    let deps_met = plan_hierarchy::dependencies_met(&conn, plan_id)?;

    if !deps_met {
        tracing::info!("ali: plan {plan_id} blocked — dependencies not met");
        actions::emit(
            pool,
            notify,
            "plan_blocked",
            &serde_json::json!({"plan_id": plan_id}),
        )?;
        return Ok(());
    }

    tracing::info!("ali: plan {plan_id} ready — delegating");
    actions::delegate_plan(pool, notify, plan_id).await
}

pub fn on_task_done(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    task_id: &str,
    plan_id: i64,
) -> AliResult {
    let conn = pool.get()?;

    let wave_id: Option<i64> = match conn.query_row(
        "SELECT wave_id FROM tasks WHERE id = ?1 AND plan_id = ?2",
        params![task_id, plan_id],
        |row| row.get(0),
    ) {
        Ok(v) => Some(v),
        Err(rusqlite::Error::QueryReturnedNoRows) => None,
        Err(e) => {
            tracing::warn!("ali: wave_id lookup for task {task_id}: {e}");
            None
        }
    };

    let Some(wave_id) = wave_id else {
        tracing::warn!("ali: task {task_id} not found in plan {plan_id}");
        return Ok(());
    };

    let pending: i64 = conn.query_row(
        "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND wave_id = ?2 \
         AND status NOT IN ('done', 'cancelled', 'skipped')",
        params![plan_id, wave_id],
        |row| row.get(0),
    )?;

    tracing::info!("ali: task {task_id} done, wave {wave_id} has {pending} remaining");

    if pending == 0 {
        actions::emit(
            pool,
            notify,
            "wave_done",
            &serde_json::json!({"wave_id": wave_id, "plan_id": plan_id}),
        )?;
    }

    Ok(())
}

pub fn on_wave_done(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    wave_id: i64,
    plan_id: i64,
) -> AliResult {
    tracing::info!("ali: wave {wave_id} complete for plan {plan_id}, requesting validation");
    actions::emit(
        pool,
        notify,
        "wave_needs_validation",
        &serde_json::json!({"wave_id": wave_id, "plan_id": plan_id}),
    )
}

pub fn on_wave_validated(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    wave_id: i64,
    plan_id: i64,
) -> AliResult {
    let conn = pool.get()?;

    let next_wave: Option<i64> = match conn.query_row(
        "SELECT id FROM waves WHERE plan_id = ?1 AND id > ?2 AND status = 'pending' \
         ORDER BY id LIMIT 1",
        params![plan_id, wave_id],
        |row| row.get(0),
    ) {
        Ok(v) => Some(v),
        Err(rusqlite::Error::QueryReturnedNoRows) => None,
        Err(e) => {
            tracing::warn!("ali: next_wave lookup for plan {plan_id}: {e}");
            None
        }
    };

    if let Some(next) = next_wave {
        tracing::info!("ali: wave {wave_id} validated, next wave {next} for plan {plan_id}");
        actions::emit(
            pool,
            notify,
            "wave_ready",
            &serde_json::json!({"wave_id": next, "plan_id": plan_id}),
        )?;
    } else {
        tracing::info!("ali: all waves validated for plan {plan_id}, plan done");
        actions::emit(
            pool,
            notify,
            "plan_done",
            &serde_json::json!({"plan_id": plan_id}),
        )?;
    }

    Ok(())
}

pub fn on_plan_done(pool: &ConnPool, notify: &Arc<Notify>, plan_id: i64) -> AliResult {
    let conn = pool.get()?;

    let parent_id: Option<i64> = match conn.query_row(
        "SELECT parent_plan_id FROM plans WHERE id = ?1",
        params![plan_id],
        |row| row.get::<_, Option<i64>>(0),
    ) {
        Ok(v) => v,
        Err(rusqlite::Error::QueryReturnedNoRows) => None,
        Err(e) => {
            tracing::warn!("ali: parent_plan_id lookup for plan {plan_id}: {e}");
            None
        }
    };

    if let Some(master_id) = parent_id {
        let (done, total, status) = plan_hierarchy::master_rollup(&conn, master_id)?;
        tracing::info!("ali: master {master_id} rollup: {done}/{total} status={status}");
        actions::check_unblocked_plans(pool, notify, &conn, master_id)?;
    }

    Ok(())
}

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
