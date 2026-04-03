// Reactor — core event loop. Blocks on IPC receive_wait, dispatches to handlers.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use convergio_ipc::messaging;

use crate::handlers;

pub const ALI_AGENT: &str = "ali-orchestrator";
pub const CHANNEL: &str = "#orchestration";

pub async fn run(pool: ConnPool, notify: Arc<Notify>) {
    loop {
        let msgs = messaging::receive_wait(
            &pool,
            &notify,
            ALI_AGENT,
            None,
            Some(CHANNEL),
            10,
            300, // 5 min keepalive
        )
        .await;

        match msgs {
            Ok(messages) => {
                for msg in &messages {
                    if msg.from_agent == ALI_AGENT {
                        continue;
                    }
                    if let Err(e) = handle_message(&pool, &notify, msg).await {
                        tracing::error!("ali: handler error for msg {}: {e}", msg.id);
                        emit_error(&pool, &notify, &e.to_string());
                    }
                }
            }
            Err(e) => {
                tracing::error!("ali: receive_wait error: {e}, retrying in 5s");
                tokio::time::sleep(std::time::Duration::from_secs(5)).await;
            }
        }
    }
}

async fn handle_message(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    msg: &convergio_ipc::types::MessageInfo,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let payload: serde_json::Value = serde_json::from_str(&msg.content)?;
    let event_type = payload
        .get("type")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown");

    tracing::info!("ali: received event={event_type} from={}", msg.from_agent);

    match event_type {
        "plan_started" | "plan_ready" => {
            let plan_id = require_i64(&payload, "plan_id")?;
            handlers::on_plan_ready(pool, notify, plan_id).await?;
        }
        "task_done" => {
            let task_id = payload
                .get("task_id")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();
            let plan_id = require_i64(&payload, "plan_id")?;
            handlers::on_task_done(pool, notify, &task_id, plan_id)?;
        }
        "wave_done" | "wave_needs_validation" => {
            let wave_id = require_i64(&payload, "wave_id")?;
            let plan_id = require_i64(&payload, "plan_id")?;
            if event_type == "wave_done" {
                handlers::on_wave_done(pool, notify, wave_id, plan_id)?;
            } else {
                tracing::info!("ali: auto-validating wave {wave_id} (Thor not yet a service)");
                handlers::on_wave_validated(pool, notify, wave_id, plan_id)?;
            }
        }
        "wave_validated" => {
            let wave_id = require_i64(&payload, "wave_id")?;
            let plan_id = require_i64(&payload, "plan_id")?;
            handlers::on_wave_validated(pool, notify, wave_id, plan_id)?;
        }
        "plan_done" => {
            let plan_id = require_i64(&payload, "plan_id")?;
            handlers::on_plan_done(pool, notify, plan_id)?;
        }
        "wave_ready" => {
            let wave_id = require_i64(&payload, "wave_id")?;
            let plan_id = require_i64(&payload, "plan_id")?;
            handlers::on_wave_ready(pool, notify, wave_id, plan_id).await?;
        }
        "delegation_failed" => {
            let plan_id = require_i64(&payload, "plan_id")?;
            let peer = payload.get("peer").and_then(|v| v.as_str()).unwrap_or("");
            let reason = payload.get("reason").and_then(|v| v.as_str()).unwrap_or("unknown");
            handlers::on_delegation_failed(pool, notify, plan_id, peer, reason).await?;
        }
        "need_human" => {
            let reason = payload.get("reason").and_then(|v| v.as_str()).unwrap_or("unknown");
            tracing::warn!("ALI NEEDS HUMAN: {reason}");
        }
        other => {
            tracing::debug!("ali: ignoring unknown event type: {other}");
        }
    }

    Ok(())
}

fn require_i64(
    payload: &serde_json::Value,
    field: &str,
) -> Result<i64, Box<dyn std::error::Error + Send + Sync>> {
    payload
        .get(field)
        .and_then(|v| v.as_i64())
        .ok_or_else(|| format!("missing or invalid field: {field}").into())
}

fn emit_error(pool: &ConnPool, notify: &Arc<Notify>, detail: &str) {
    let content = serde_json::json!({"type": "error", "detail": detail}).to_string();
    if let Err(e) = messaging::broadcast(pool, notify, ALI_AGENT, &content, "error", Some(CHANNEL), 100) {
        tracing::warn!("ali: emit_error broadcast failed: {e}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn require_i64_extracts_valid_field() {
        let payload = serde_json::json!({"plan_id": 719});
        assert_eq!(require_i64(&payload, "plan_id").unwrap(), 719);
    }

    #[test]
    fn require_i64_errors_on_missing() {
        let payload = serde_json::json!({"other": 1});
        assert!(require_i64(&payload, "plan_id").is_err());
    }

    #[test]
    fn require_i64_errors_on_string() {
        let payload = serde_json::json!({"plan_id": "not_a_number"});
        assert!(require_i64(&payload, "plan_id").is_err());
    }
}
