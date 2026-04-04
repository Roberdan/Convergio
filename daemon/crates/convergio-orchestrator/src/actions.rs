// Actions — reusable functions for peer discovery, delegation, and event emission.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use convergio_ipc::messaging;

use crate::reactor::CHANNEL;

type AliResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

pub const DAEMON_BASE: &str = "http://localhost:8420";

/// Find an available online peer from mesh status.
/// Optionally exclude a specific peer (for retry after failure).
pub async fn find_available_peer(exclude: Option<&str>) -> Option<String> {
    let url = format!("{DAEMON_BASE}/api/mesh/status");
    let mut resp = None;
    for attempt in 0..3 {
        match reqwest::get(&url).await {
            Ok(r) => {
                resp = Some(r);
                break;
            }
            Err(e) => {
                if attempt < 2 {
                    tracing::debug!(
                        "ali: mesh status attempt {}, retrying in 2s: {e}",
                        attempt + 1
                    );
                    tokio::time::sleep(std::time::Duration::from_secs(2)).await;
                } else {
                    tracing::warn!("ali: mesh status failed after 3 attempts: {e}");
                    return None;
                }
            }
        }
    }
    let resp = resp?;

    let body: serde_json::Value = match resp.json().await {
        Ok(v) => v,
        Err(e) => {
            tracing::warn!("ali: mesh status parse failed: {e}");
            return None;
        }
    };

    let peers = body.get("peers")?.as_array()?;
    for peer in peers {
        let name = peer.get("peer_name")?.as_str()?;
        let online = peer
            .get("is_online")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        if online && (exclude != Some(name)) {
            return Some(name.to_string());
        }
    }
    None
}

/// Delegate a plan to the best available peer.
pub async fn delegate_plan(pool: &ConnPool, notify: &Arc<Notify>, plan_id: i64) -> AliResult {
    let peer = find_available_peer(None).await;

    let Some(peer_name) = peer else {
        tracing::warn!("ali: no peers available for plan {plan_id}");
        emit(
            pool,
            notify,
            "need_human",
            &serde_json::json!({
                "plan_id": plan_id,
                "reason": "no online peers available for delegation",
            }),
        )?;
        return Ok(());
    };

    crate::executor::delegate_to_peer(pool, notify, plan_id, &peer_name).await
}

/// Check for sibling plans now unblocked after a plan completes.
pub fn check_unblocked_plans(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    conn: &rusqlite::Connection,
    master_id: i64,
) -> AliResult {
    let mut stmt =
        conn.prepare("SELECT id FROM plans WHERE parent_plan_id = ?1 AND status = 'todo'")?;

    let plan_ids: Vec<i64> = stmt
        .query_map(rusqlite::params![master_id], |row| row.get(0))?
        .filter_map(|r| r.ok())
        .collect();

    for pid in plan_ids {
        if crate::plan_hierarchy::dependencies_met(conn, pid)? {
            tracing::info!("ali: plan {pid} now unblocked under master {master_id}");
            emit(
                pool,
                notify,
                "plan_ready",
                &serde_json::json!({"plan_id": pid}),
            )?;
        }
    }

    Ok(())
}

/// Emit a structured event to the #orchestration channel.
/// Uses "orchestrator-reactor" as sender so the reactor (ali-orchestrator)
/// picks up the message. The reactor skips messages from ALI_AGENT (itself).
pub fn emit(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    event_type: &str,
    payload: &serde_json::Value,
) -> AliResult {
    let mut content = payload.clone();
    if let Some(obj) = content.as_object_mut() {
        obj.insert("type".to_string(), serde_json::json!(event_type));
    }
    messaging::broadcast(
        pool,
        notify,
        "orchestrator-reactor",
        &content.to_string(),
        "event",
        Some(CHANNEL),
        100,
    )?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> (ConnPool, Arc<Notify>) {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "ipc",
            &convergio_ipc::schema::migrations(),
        )
        .unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "orchestrator",
            &crate::schema::migrations(),
        )
        .unwrap();
        (pool, Arc::new(Notify::new()))
    }

    #[test]
    fn emit_broadcasts_to_channel() {
        let (pool, notify) = setup();
        let result = emit(
            &pool,
            &notify,
            "plan_delegated",
            &serde_json::json!({"plan_id": 42, "peer": "macProM1"}),
        );
        assert!(result.is_ok());

        let history = messaging::history(&pool, None, Some(CHANNEL), 10, None).unwrap();
        assert!(!history.is_empty());
        assert!(history[0].content.contains("plan_delegated"));
    }

    #[test]
    fn check_unblocked_with_no_children() {
        let (pool, notify) = setup();
        let conn = pool.get().unwrap();
        let result = check_unblocked_plans(&pool, &notify, &conn, 999);
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn find_peer_returns_none_when_daemon_not_running() {
        let peer = find_available_peer(None).await;
        assert!(peer.is_none());
    }
}
