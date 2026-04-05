//! HTTP routes for self-build operations.

use crate::builder;
use crate::types::{BuildRecord, BuildStatus};
use axum::extract::{Path, Query, State};
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};
use std::sync::Arc;
use std::time::Instant;

/// Shared state for build routes.
#[derive(Clone)]
pub struct BuildState {
    pub pool: ConnPool,
}

/// Build the self-build router.
pub fn router(state: Arc<BuildState>) -> Router {
    Router::new()
        .route("/api/build/self", post(trigger_build))
        .route("/api/build/status/{id}", get(build_status))
        .route("/api/build/history", get(build_history))
        .route("/api/build/deploy/{id}", post(deploy_build))
        .route("/api/build/rollback", post(rollback_build))
        .with_state(state)
}

/// POST /api/build/self — Trigger a new self-build.
async fn trigger_build(State(st): State<Arc<BuildState>>) -> Json<Value> {
    let commit = builder::current_commit();
    let build_id = match builder::create_build(&st.pool, &commit) {
        Ok(id) => id,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };

    let pool = st.pool.clone();
    let id = build_id.clone();

    // Run build in background task
    tokio::spawn(async move {
        run_build_pipeline(pool, id).await;
    });

    Json(json!({
        "ok": true,
        "build_id": build_id,
        "commit": commit,
        "status": "queued"
    }))
}

/// Background build pipeline: check → test → build → update DB.
async fn run_build_pipeline(pool: ConnPool, build_id: String) {
    let start = Instant::now();
    let workspace = builder::workspace_root();

    // Mark as building
    let _ = builder::update_status(&pool, &build_id, BuildStatus::Building);

    // Run build (blocking — offload to spawn_blocking)
    let ws = workspace.clone();
    let result = tokio::task::spawn_blocking(move || builder::run_build(&ws)).await;

    let duration = start.elapsed().as_secs_f64();
    let commit = builder::current_commit();

    match result {
        Ok(Ok((test_count, binary_hash, binary_size))) => {
            let record = BuildRecord {
                id: build_id.clone(),
                status: BuildStatus::Succeeded,
                commit_hash: commit,
                test_count: Some(test_count),
                binary_hash: Some(binary_hash),
                binary_size: Some(binary_size),
                started_at: String::new(),
                completed_at: None,
                error: None,
                duration_secs: Some(duration),
            };
            let _ = builder::complete_build(&pool, &build_id, &record);
            tracing::info!(build_id, duration, test_count, "self-build succeeded");
        }
        Ok(Err(e)) => {
            let record = BuildRecord {
                id: build_id.clone(),
                status: BuildStatus::Failed,
                commit_hash: commit,
                test_count: None,
                binary_hash: None,
                binary_size: None,
                started_at: String::new(),
                completed_at: None,
                error: Some(e.to_string()),
                duration_secs: Some(duration),
            };
            let _ = builder::complete_build(&pool, &build_id, &record);
            tracing::error!(build_id, error = %e, "self-build failed");
        }
        Err(e) => {
            tracing::error!(build_id, error = %e, "self-build task panicked");
        }
    }
}

/// GET /api/build/status/:id — Get build status.
async fn build_status(State(st): State<Arc<BuildState>>, Path(id): Path<String>) -> Json<Value> {
    match builder::get_build(&st.pool, &id) {
        Ok(rec) => Json(json!({"ok": true, "build": rec})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct HistoryQuery {
    #[serde(default = "default_limit")]
    limit: i64,
}

fn default_limit() -> i64 {
    20
}

/// GET /api/build/history — List recent builds.
async fn build_history(
    State(st): State<Arc<BuildState>>,
    Query(q): Query<HistoryQuery>,
) -> Json<Value> {
    match builder::list_builds(&st.pool, q.limit) {
        Ok(builds) => Json(json!({"ok": true, "builds": builds})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

/// POST /api/build/deploy/:id — Deploy a successful build.
async fn deploy_build(State(st): State<Arc<BuildState>>, Path(id): Path<String>) -> Json<Value> {
    // Verify build succeeded
    let record = match builder::get_build(&st.pool, &id) {
        Ok(r) => r,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    if record.status != BuildStatus::Succeeded {
        return Json(json!({
            "ok": false,
            "error": format!("build status is '{}', must be 'succeeded'", record.status)
        }));
    }

    let workspace = builder::workspace_root();
    match crate::deployer::deploy(&workspace) {
        Ok(backup) => {
            let _ = builder::update_status(&st.pool, &id, BuildStatus::Deployed);
            Json(json!({
                "ok": true,
                "deployed": true,
                "backup": backup.to_string_lossy(),
                "note": "daemon will restart via launchd"
            }))
        }
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

/// POST /api/build/rollback — Rollback to previous binary.
async fn rollback_build(State(_st): State<Arc<BuildState>>) -> Json<Value> {
    let workspace = builder::workspace_root();
    match crate::deployer::rollback(&workspace) {
        Ok(()) => Json(json!({
            "ok": true,
            "rolled_back": true,
            "note": "daemon will restart with previous binary"
        })),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}
