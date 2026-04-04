//! HTTP API routes for the node capability registry.
//!
//! - POST   /api/mesh/capabilities/:peer_name  — register capabilities
//! - GET    /api/mesh/capabilities              — list all capabilities
//! - GET    /api/mesh/capabilities/:peer_name   — get peer capabilities
//! - DELETE /api/mesh/capabilities/:peer_name   — remove peer capabilities
//! - POST   /api/mesh/capabilities/query        — find capable peers

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde_json::json;

use convergio_db::pool::ConnPool;

use crate::capability_registry;
use crate::capability_types::{CapabilityQuery, NodeCapability};

struct CapState {
    pool: ConnPool,
}

pub fn capability_routes(pool: ConnPool) -> Router {
    let state = Arc::new(CapState { pool });
    Router::new()
        .route("/api/mesh/capabilities/query", post(handle_query))
        .route(
            "/api/mesh/capabilities/:peer_name",
            post(handle_register)
                .get(handle_get_peer)
                .delete(handle_delete_peer),
        )
        .route("/api/mesh/capabilities", get(handle_list_all))
        .with_state(state)
}

async fn handle_register(
    State(state): State<Arc<CapState>>,
    Path(peer_name): Path<String>,
    Json(caps): Json<Vec<NodeCapability>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match capability_registry::register_capabilities(&conn, &peer_name, &caps) {
        Ok(()) => Json(json!({"status": "ok", "registered": caps.len()})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_list_all(State(state): State<Arc<CapState>>) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match capability_registry::list_all_capabilities(&conn) {
        Ok(all) => Json(json!(all)),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_get_peer(
    State(state): State<Arc<CapState>>,
    Path(peer_name): Path<String>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match capability_registry::get_peer_capabilities(&conn, &peer_name) {
        Ok(caps) => Json(json!(caps)),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_delete_peer(
    State(state): State<Arc<CapState>>,
    Path(peer_name): Path<String>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match capability_registry::remove_peer_capabilities(&conn, &peer_name) {
        Ok(()) => Json(json!({"status": "ok"})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_query(
    State(state): State<Arc<CapState>>,
    Json(query): Json<CapabilityQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match capability_registry::query_capable_peers(&conn, &query) {
        Ok(matches) => Json(json!(matches)),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}
