//! HTTP routes for the delegation API.

use axum::extract::{Path, Query, State};
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::types::{DelegateMarkRequest, DelegateRequest, PipelineConfig};
use crate::{pipeline, queries};

/// Query parameters for listing delegations.
#[derive(Deserialize)]
pub struct ListParams {
    pub plan_id: Option<i64>,
    pub limit: Option<u32>,
}

/// Build the delegation router.
pub fn delegation_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/mesh/delegate", post(mark_delegated))
        .route("/api/delegate/spawn", post(spawn_delegation))
        .route("/api/delegate/status/:delegation_id", get(get_status))
        .route("/api/delegate/list", get(list_delegations))
        .with_state(pool)
}

/// POST /api/mesh/delegate — mark a plan as delegated to a peer.
async fn mark_delegated(
    State(pool): State<ConnPool>,
    Json(req): Json<DelegateMarkRequest>,
) -> Json<Value> {
    let delegation_id = uuid::Uuid::new_v4().to_string();
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO delegations (delegation_id, plan_id, peer_name) VALUES (?1, ?2, ?3)",
        rusqlite::params![delegation_id, req.plan_id, req.peer],
    ) {
        Ok(_) => Json(json!({
            "ok": true,
            "delegation_id": delegation_id,
            "status": "marked"
        })),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

/// POST /api/delegate/spawn — create delegation record and launch pipeline.
async fn spawn_delegation(
    State(pool): State<ConnPool>,
    Json(req): Json<DelegateRequest>,
) -> Json<Value> {
    let delegation_id = uuid::Uuid::new_v4().to_string();

    // Resolve project root from env or cwd
    let project_root = std::env::var("CONVERGIO_PROJECT_ROOT").unwrap_or_else(|_| {
        std::env::current_dir()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| ".".to_string())
    });
    let config = PipelineConfig {
        project_root: project_root.clone(),
        ..PipelineConfig::default()
    };

    // Insert delegation record
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    if let Err(e) = conn.execute(
        "INSERT INTO delegations (delegation_id, plan_id, peer_name, source_path) \
         VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![delegation_id, req.plan_id, req.peer, project_root],
    ) {
        return Json(json!({"ok": false, "error": e.to_string()}));
    }
    drop(conn);

    // Spawn pipeline in background
    let pool_bg = pool.clone();
    let del_id = delegation_id.clone();
    let peer = req.peer.clone();
    tokio::spawn(async move {
        if let Err(e) =
            pipeline::run_delegation_pipeline(&pool_bg, &del_id, req.plan_id, &peer, &config).await
        {
            tracing::error!(delegation_id = %del_id, error = %e, "delegation pipeline failed");
            let fail = crate::types::DelegationStatus::Failed(e.to_string());
            let step = crate::types::DelegationStep::Init;
            let _ = queries::update_delegation_status(&pool_bg, &del_id, &fail, &step);
        }
    });

    Json(json!({
        "ok": true,
        "delegation_id": delegation_id,
        "status": "started"
    }))
}

/// GET /api/delegate/status/:delegation_id
async fn get_status(
    State(pool): State<ConnPool>,
    Path(delegation_id): Path<String>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    match queries::get_delegation(&conn, &delegation_id) {
        Some(rec) => Json(json!({"ok": true, "delegation": rec})),
        None => Json(json!({"ok": false, "error": "delegation not found"})),
    }
}

/// GET /api/delegate/list?plan_id=N&limit=50
async fn list_delegations(
    State(pool): State<ConnPool>,
    Query(params): Query<ListParams>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    let limit = params.limit.unwrap_or(50).min(100);
    let list = queries::list_delegations(&conn, params.plan_id, limit);
    Json(json!({"ok": true, "delegations": list}))
}
