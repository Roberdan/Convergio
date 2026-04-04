//! HTTP routes for mesh — status, peers, sync, delegation.

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::json;

/// Build all mesh routes.
pub fn mesh_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/mesh", get(mesh_status))
        .route("/api/mesh/sync-stats", get(sync_stats))
        .route("/api/mesh/peers", get(list_peers))
        .route("/api/mesh/convergence", get(convergence_check))
        .route("/api/mesh/delegation/{id}", get(delegation_progress))
        .route("/api/mesh/delegation", post(record_delegation_step))
        .with_state(pool)
}

async fn mesh_status(State(pool): State<ConnPool>) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let peers: i64 = conn
        .query_row(
            "SELECT count(DISTINCT peer_name) FROM mesh_sync_stats",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let total_synced: i64 = conn
        .query_row(
            "SELECT COALESCE(sum(total_sent + total_received), 0) FROM mesh_sync_stats",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    ok(json!({"peers": peers, "total_synced": total_synced}))
}

async fn sync_stats(State(pool): State<ConnPool>) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let mut stmt = conn
        .prepare(
            "SELECT peer_name, total_sent, total_received, total_applied, \
             last_latency_ms, last_sync_at FROM mesh_sync_stats \
             ORDER BY last_sync_at DESC LIMIT 100",
        )
        .map_err(|e| err(e))?;
    let rows: Vec<serde_json::Value> = stmt
        .query_map([], |r| {
            Ok(json!({
                "peer": r.get::<_, String>(0)?,
                "sent": r.get::<_, i64>(1)?,
                "received": r.get::<_, i64>(2)?,
                "applied": r.get::<_, i64>(3)?,
                "latency_ms": r.get::<_, Option<i64>>(4)?,
                "synced_at": r.get::<_, Option<String>>(5)?,
            }))
        })
        .map_err(|e| err(e))?
        .filter_map(|r| r.ok())
        .collect();
    ok(json!(rows))
}

async fn list_peers(State(_pool): State<ConnPool>) -> impl IntoResponse {
    let path = crate::peers_registry::peers_conf_path_from_env();
    match crate::peers_types::PeersRegistry::load(std::path::Path::new(&path)) {
        Ok(registry) => {
            let peers: Vec<serde_json::Value> = registry
                .list_active()
                .iter()
                .map(|(name, cfg)| {
                    json!({
                        "name": name,
                        "role": &cfg.role,
                        "status": &cfg.status,
                        "tailscale_ip": &cfg.tailscale_ip,
                    })
                })
                .collect();
            ok(json!(peers))
        }
        Err(e) => Err(err(e)),
    }
}

async fn convergence_check(State(pool): State<ConnPool>) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let checksum = crate::convergence::compute_local_checksum(&conn);
    ok(json!({"local_checksum": checksum}))
}

async fn delegation_progress(
    State(pool): State<ConnPool>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let progress = crate::delegation::get_progress(&conn, &id);
    ok(json!({"delegation_id": id, "progress": progress}))
}

#[derive(Deserialize)]
struct DelegationStepReq {
    delegation_id: String,
    step: String,
    status: String,
    summary: Option<String>,
}

async fn record_delegation_step(
    State(pool): State<ConnPool>,
    Json(r): Json<DelegationStepReq>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    crate::delegation::record_step(
        &conn,
        &r.delegation_id,
        &r.step,
        &r.status,
        r.summary.as_deref(),
    );
    ok(json!({"ok": true}))
}

fn err(e: impl std::fmt::Display) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, e.to_string())
}

fn ok(v: serde_json::Value) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    Ok(Json(v))
}
