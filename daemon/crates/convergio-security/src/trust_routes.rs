//! HTTP API routes for trust, secrets filtering, and sandbox policies.

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::Deserialize;

use convergio_db::pool::ConnPool;

use crate::sandbox::{self, SandboxPolicy};
use crate::trust::{self, PeerTrustRecord, SecretFilter, TrustLevel};

/// Shared state for security routes.
pub struct SecurityState {
    pub pool: ConnPool,
}

/// Build the security trust/sandbox API router.
pub fn security_routes(state: Arc<SecurityState>) -> Router {
    Router::new()
        .route("/api/security/trust", post(handle_set_trust))
        .route("/api/security/trust", get(handle_list_trust))
        .route("/api/security/trust/:peer", get(handle_get_trust))
        .route("/api/security/secrets/filter", post(handle_register_filter))
        .route("/api/security/secrets/filter", get(handle_list_filters))
        .route("/api/security/sandbox/:peer", get(handle_get_sandbox))
        .route("/api/security/sandbox/:peer", post(handle_set_sandbox))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct SetTrustRequest {
    pub peer: String,
    pub level: i64,
    pub granted_by: String,
    pub reason: String,
}

async fn handle_set_trust(
    State(state): State<Arc<SecurityState>>,
    Json(body): Json<SetTrustRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let level = TrustLevel::from_i64(body.level);
    if let Err(e) = trust::set_trust(&conn, &body.peer, level, &body.granted_by, &body.reason) {
        return Json(err_json("DB_ERROR", &e.to_string()));
    }
    Json(serde_json::json!({
        "status": "ok",
        "peer": body.peer,
        "trust_level": level as i64,
    }))
}

async fn handle_get_trust(
    State(state): State<Arc<SecurityState>>,
    Path(peer): Path<String>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let level = trust::get_trust(&conn, &peer);
    Json(serde_json::json!({
        "peer": peer,
        "trust_level": level as i64,
    }))
}

async fn handle_list_trust(State(state): State<Arc<SecurityState>>) -> Json<Vec<PeerTrustRecord>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    Json(trust::list_trust(&conn))
}

#[derive(Debug, Deserialize)]
pub struct RegisterFilterRequest {
    pub env_var: String,
    pub min_trust_level: i64,
    pub description: String,
}

async fn handle_register_filter(
    State(state): State<Arc<SecurityState>>,
    Json(body): Json<RegisterFilterRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let level = TrustLevel::from_i64(body.min_trust_level);
    if let Err(e) = trust::register_secret_filter(&conn, &body.env_var, level, &body.description) {
        return Json(err_json("DB_ERROR", &e.to_string()));
    }
    Json(serde_json::json!({"status": "ok", "env_var": body.env_var}))
}

async fn handle_list_filters(State(state): State<Arc<SecurityState>>) -> Json<Vec<SecretFilter>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    Json(trust::list_secret_filters(&conn))
}

async fn handle_get_sandbox(
    State(state): State<Arc<SecurityState>>,
    Path(peer): Path<String>,
) -> Json<SandboxPolicy> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(sandbox::sandbox_for_trust(&peer, TrustLevel::Untrusted)),
    };
    let trust_level = trust::get_trust(&conn, &peer);
    Json(sandbox::resolve_sandbox(&conn, &peer, trust_level))
}

async fn handle_set_sandbox(
    State(state): State<Arc<SecurityState>>,
    Path(peer): Path<String>,
    Json(mut body): Json<SandboxPolicy>,
) -> Json<serde_json::Value> {
    body.peer_name = peer.clone();
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    if let Err(e) = sandbox::set_custom_sandbox(&conn, &body) {
        return Json(err_json("DB_ERROR", &e.to_string()));
    }
    Json(serde_json::json!({"status": "ok", "peer": peer}))
}

fn err_json(code: &str, message: &str) -> serde_json::Value {
    serde_json::json!({"error": {"code": code, "message": message}})
}
