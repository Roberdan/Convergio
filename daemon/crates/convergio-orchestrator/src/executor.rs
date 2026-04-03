// Executor — delegates plan execution to a mesh peer via HTTP API.
// Uses daemon API for rsync, prompt delivery, and tmux launch.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use convergio_ipc::messaging;

use crate::actions::DAEMON_BASE;
use crate::reactor::{ALI_AGENT, CHANNEL};

type AliResult = Result<(), Box<dyn std::error::Error + Send + Sync>>;

/// Delegate a plan to a specific peer via daemon API:
/// 1. Mark plan as delegated in DB
/// 2. Trigger delegation pipeline on daemon
/// 3. Emit plan_delegated event
pub async fn delegate_to_peer(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    plan_id: i64,
    peer: &str,
) -> AliResult {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .unwrap_or_default();

    tracing::info!("ali: delegating plan {plan_id} to peer {peer}");

    // Mark plan in DB via API
    if let Err(e) = client
        .post(format!("{DAEMON_BASE}/api/mesh/delegate"))
        .json(&serde_json::json!({"plan_id": plan_id, "peer": peer}))
        .send()
        .await
    {
        tracing::warn!("ali: delegate mark in DB failed: {e}");
    }

    // Trigger the delegation pipeline via daemon API
    let session = "Convergio";
    let window = format!("plan-{plan_id}");

    let spawn_resp = client
        .post(format!("{DAEMON_BASE}/api/delegate/spawn"))
        .json(&serde_json::json!({
            "peer": peer,
            "plan_id": plan_id,
            "tmux_session": session,
            "tmux_window": &window,
        }))
        .send()
        .await?;

    if !spawn_resp.status().is_success() {
        return Err(format!("delegate spawn failed: {}", spawn_resp.status()).into());
    }

    tracing::info!("ali: plan {plan_id} launched on {peer} in tmux:{session}:{window}");

    let mut content = serde_json::json!({
        "plan_id": plan_id,
        "peer": peer,
        "tmux_session": session,
        "tmux_window": window,
    });
    content.as_object_mut().unwrap().insert("type".to_string(), serde_json::json!("plan_delegated"));

    messaging::broadcast(pool, notify, ALI_AGENT, &content.to_string(), "event", Some(CHANNEL), 100)?;
    Ok(())
}
