//! HTTP API routes for multi-tenancy isolation.
//!
//! - GET  /api/tenancy/policy       — get isolation policy for org
//! - GET  /api/tenancy/peers        — list peer whitelist
//! - POST /api/tenancy/peers        — add/revoke peer
//! - GET  /api/tenancy/secrets      — list secret keys for org
//! - GET  /api/tenancy/audit        — query org audit trail
//! - GET  /api/tenancy/resources    — resource limits and usage
//! - POST /api/tenancy/resources    — set resource limits

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::{Deserialize, Serialize};

use convergio_db::pool::ConnPool;

use crate::types::OrgId;
use crate::{audit_isolation, network_isolation, resource_limits, secret_isolation};

/// Shared state for tenancy routes.
pub struct TenancyState {
    pub pool: ConnPool,
}

/// Build the tenancy API router.
pub fn tenancy_routes(state: Arc<TenancyState>) -> Router {
    Router::new()
        .route("/api/tenancy/peers", get(handle_list_peers))
        .route("/api/tenancy/peers", post(handle_manage_peer))
        .route("/api/tenancy/secrets", get(handle_list_secrets))
        .route("/api/tenancy/audit", get(handle_audit))
        .route("/api/tenancy/resources", get(handle_resources))
        .route("/api/tenancy/resources", post(handle_set_limits))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct OrgQuery {
    pub org_id: String,
}

#[derive(Debug, Deserialize)]
pub struct PeerAction {
    pub org_id: String,
    pub peer_name: String,
    pub peer_url: Option<String>,
    pub action: String,
}

#[derive(Debug, Serialize)]
pub struct PeerEntry {
    pub peer_name: String,
    pub peer_url: String,
    pub allowed: bool,
}

async fn handle_list_peers(
    State(state): State<Arc<TenancyState>>,
    Query(params): Query<OrgQuery>,
) -> Json<Vec<PeerEntry>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    let org = OrgId(params.org_id);
    let peers = network_isolation::list_peers(&conn, &org).unwrap_or_default();
    Json(
        peers
            .into_iter()
            .map(|p| PeerEntry {
                peer_name: p.peer_name,
                peer_url: p.peer_url,
                allowed: p.allowed,
            })
            .collect(),
    )
}

async fn handle_manage_peer(
    State(state): State<Arc<TenancyState>>,
    Json(body): Json<PeerAction>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": {"code": "POOL_ERROR", "message": e.to_string()}
            }))
        }
    };
    let org = OrgId(body.org_id);
    let result = match body.action.as_str() {
        "allow" => {
            let url = body.peer_url.as_deref().unwrap_or("");
            network_isolation::allow_peer(&conn, &org, &body.peer_name, url)
        }
        "revoke" => network_isolation::revoke_peer(&conn, &org, &body.peer_name),
        other => {
            return Json(serde_json::json!({
                "error": {"code": "INVALID_ACTION", "message": other}
            }))
        }
    };
    match result {
        Ok(()) => Json(serde_json::json!({"status": "ok"})),
        Err(e) => Json(serde_json::json!({
            "error": {"code": "DB_ERROR", "message": e.to_string()}
        })),
    }
}

async fn handle_list_secrets(
    State(state): State<Arc<TenancyState>>,
    Query(params): Query<OrgQuery>,
) -> Json<Vec<String>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    let org = OrgId(params.org_id);
    Json(secret_isolation::list_secret_keys(&conn, &org).unwrap_or_default())
}

#[derive(Debug, Deserialize)]
pub struct AuditQuery {
    pub org_id: Option<String>,
    pub limit: Option<u32>,
}

async fn handle_audit(
    State(state): State<Arc<TenancyState>>,
    Query(params): Query<AuditQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(serde_json::json!([])),
    };
    let limit = params.limit.unwrap_or(50);
    let entries = match &params.org_id {
        Some(id) => {
            let org = OrgId(id.clone());
            audit_isolation::query_org(&conn, &org, limit).unwrap_or_default()
        }
        None => audit_isolation::query_all(&conn, limit).unwrap_or_default(),
    };
    Json(serde_json::to_value(entries).unwrap_or_default())
}

#[derive(Debug, Serialize)]
pub struct ResourceStatus {
    pub org_id: String,
    pub limits: Option<serde_json::Value>,
    pub usage: Option<serde_json::Value>,
    pub violations: Vec<String>,
}

async fn handle_resources(
    State(state): State<Arc<TenancyState>>,
    Query(params): Query<OrgQuery>,
) -> Json<ResourceStatus> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => {
            return Json(ResourceStatus {
                org_id: params.org_id,
                limits: None,
                usage: None,
                violations: vec![],
            })
        }
    };
    let org = OrgId(params.org_id.clone());
    let limits = resource_limits::get_limits(&conn, &org)
        .ok()
        .flatten()
        .and_then(|l| serde_json::to_value(l).ok());
    let usage = resource_limits::latest_usage(&conn, &org)
        .ok()
        .flatten()
        .and_then(|u| serde_json::to_value(u).ok());
    let violations = resource_limits::check_limits(&conn, &org).unwrap_or_default();
    Json(ResourceStatus {
        org_id: params.org_id,
        limits,
        usage,
        violations,
    })
}

#[derive(Debug, Deserialize)]
pub struct SetLimitsRequest {
    pub org_id: String,
    pub max_cpu_seconds_per_hour: Option<u64>,
    pub max_memory_mb: Option<u64>,
    pub max_storage_mb: Option<u64>,
    pub max_concurrent_agents: Option<u32>,
    pub max_api_calls_per_minute: Option<u32>,
}

async fn handle_set_limits(
    State(state): State<Arc<TenancyState>>,
    Json(body): Json<SetLimitsRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": {"code": "POOL_ERROR", "message": e.to_string()}
            }))
        }
    };
    let org = OrgId(body.org_id);
    let mut limits = crate::types::ResourceLimits::default_for(org.clone());
    if let Some(v) = body.max_cpu_seconds_per_hour {
        limits.max_cpu_seconds_per_hour = v;
    }
    if let Some(v) = body.max_memory_mb {
        limits.max_memory_mb = v;
    }
    if let Some(v) = body.max_storage_mb {
        limits.max_storage_mb = v;
    }
    if let Some(v) = body.max_concurrent_agents {
        limits.max_concurrent_agents = v;
    }
    if let Some(v) = body.max_api_calls_per_minute {
        limits.max_api_calls_per_minute = v;
    }
    match resource_limits::set_limits(&conn, &limits) {
        Ok(()) => Json(serde_json::json!({"status": "ok"})),
        Err(e) => Json(serde_json::json!({
            "error": {"code": "DB_ERROR", "message": e.to_string()}
        })),
    }
}
