//! HTTP API routes for mesh sync and peer management.
//!
//! - GET  /api/mesh           — mesh status (peers online, sync stats)
//! - GET  /api/mesh/peers     — list peers from heartbeat table
//! - GET  /api/sync/export    — export changes since timestamp (query: table, since)
//! - POST /api/sync/import    — apply SyncChange[] from a peer
//! - GET  /api/sync/status    — sync metadata per peer
//! - POST /api/heartbeat      — receive heartbeat from a peer

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use rusqlite::params;
use serde::Deserialize;
use serde_json::json;

use convergio_db::pool::ConnPool;

use crate::sync_apply;
use crate::types::SyncChange;

pub struct MeshState {
    pub pool: ConnPool,
}

pub fn mesh_routes(state: Arc<MeshState>) -> Router {
    Router::new()
        .route("/api/mesh", get(handle_status))
        .route("/api/mesh/peers", get(handle_peers))
        .route("/api/sync/export", get(handle_export))
        .route("/api/sync/import", post(handle_import))
        .route("/api/sync/status", get(handle_sync_status))
        .route("/api/heartbeat", post(handle_heartbeat))
        .with_state(state)
}

async fn handle_status(
    State(state): State<Arc<MeshState>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let peers_online: u64 = conn
        .query_row(
            "SELECT count(*) FROM peer_heartbeats \
             WHERE last_seen > unixepoch() - 600",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let total_synced: u64 = conn
        .query_row(
            "SELECT COALESCE(SUM(total_applied), 0) FROM mesh_sync_stats",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    Json(json!({
        "peers_online": peers_online,
        "total_synced": total_synced,
    }))
}

async fn handle_peers(
    State(state): State<Arc<MeshState>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT peer_name, last_seen, version, \
         CASE WHEN last_seen > unixepoch() - 600 THEN 'online' \
         ELSE 'offline' END as status \
         FROM peer_heartbeats ORDER BY peer_name",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let peers: Vec<serde_json::Value> = match stmt.query_map([], |row| {
        Ok(json!({
            "peer": row.get::<_, String>(0)?,
            "last_seen": row.get::<_, i64>(1)?,
            "version": row.get::<_, Option<String>>(2)?,
            "status": row.get::<_, String>(3)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!(peers))
}

#[derive(Debug, Deserialize)]
pub struct ExportQuery {
    pub table: String,
    pub since: Option<String>,
}

async fn handle_export(
    State(state): State<Arc<MeshState>>,
    Query(params): Query<ExportQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match sync_apply::export_changes_since(
        &conn,
        &params.table,
        params.since.as_deref(),
    ) {
        Ok(changes) => Json(json!({"changes": changes})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_import(
    State(state): State<Arc<MeshState>>,
    Json(changes): Json<Vec<SyncChange>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match sync_apply::apply_changes(&conn, &changes) {
        Ok(applied) => Json(json!({"applied": applied})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_sync_status(
    State(state): State<Arc<MeshState>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT peer_name, total_applied, last_sync_at, \
         last_latency_ms, consecutive_failures \
         FROM mesh_sync_stats ORDER BY peer_name",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<serde_json::Value> = match stmt.query_map([], |row| {
        Ok(json!({
            "peer": row.get::<_, String>(0)?,
            "total_applied": row.get::<_, i64>(1)?,
            "last_sync_at": row.get::<_, Option<String>>(2)?,
            "latency_ms": row.get::<_, Option<i64>>(3)?,
            "failures": row.get::<_, i64>(4)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!(rows))
}

#[derive(Debug, Deserialize)]
pub struct HeartbeatRequest {
    pub peer: String,
    #[serde(default)]
    pub version: Option<String>,
    #[serde(default)]
    pub capabilities: Option<String>,
}

async fn handle_heartbeat(
    State(state): State<Arc<MeshState>>,
    Json(body): Json<HeartbeatRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO peer_heartbeats (peer_name, last_seen, version, capabilities) \
         VALUES (?1, unixepoch(), ?2, ?3) \
         ON CONFLICT(peer_name) DO UPDATE SET \
         last_seen = unixepoch(), version = excluded.version, \
         capabilities = excluded.capabilities",
        params![body.peer, body.version, body.capabilities],
    ) {
        Ok(_) => Json(json!({"status": "ok"})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}
