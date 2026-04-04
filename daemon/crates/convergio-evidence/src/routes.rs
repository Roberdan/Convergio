//! HTTP routes for evidence — record, query, gates, preflight.

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::json;

/// Build all evidence routes.
pub fn evidence_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/evidence", post(record_evidence))
        .route("/api/evidence/{task_id}", get(list_evidence))
        .route("/api/evidence/{task_id}/has/{kind}", get(has_evidence))
        .route("/api/evidence/{task_id}/commits", get(list_commits))
        .route("/api/evidence/gates/{task_id}", post(run_gates))
        .route("/api/evidence/preflight/{task_id}", get(run_preflight))
        .route("/api/evidence/commit-match", post(match_commit))
        .with_state(pool)
}

#[derive(Deserialize)]
struct RecordReq {
    task_id: i64,
    evidence_type: String,
    command: String,
    output_summary: String,
    exit_code: i64,
}

async fn record_evidence(
    State(pool): State<ConnPool>,
    Json(r): Json<RecordReq>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let id = crate::evidence::record_evidence(
        &conn,
        r.task_id,
        &r.evidence_type,
        &r.command,
        &r.output_summary,
        r.exit_code,
    )
    .map_err(|e| err(e))?;
    ok_created(json!({"id": id}))
}

async fn list_evidence(
    State(pool): State<ConnPool>,
    Path(task_id): Path<i64>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let records = crate::evidence::list_evidence(&conn, task_id);
    ok(json!(records))
}

async fn has_evidence(
    State(pool): State<ConnPool>,
    Path((task_id, kind)): Path<(i64, String)>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let exists = crate::evidence::has_evidence(&conn, task_id, &kind);
    ok(json!({"has_evidence": exists}))
}

async fn list_commits(State(pool): State<ConnPool>, Path(task_id): Path<i64>) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let commits = crate::evidence::list_commit_matches(&conn, task_id);
    ok(json!(commits))
}

#[derive(Deserialize)]
struct GateReq {
    #[serde(default = "default_target")]
    target_status: String,
}

fn default_target() -> String {
    "submitted".into()
}

async fn run_gates(
    State(pool): State<ConnPool>,
    Path(task_id): Path<i64>,
    Json(r): Json<GateReq>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    match crate::gates::run_all_gates(&conn, task_id, &r.target_status) {
        Ok(()) => ok(json!({"passed": true})),
        Err(violation) => Ok(Json(
            json!({"passed": false, "violation": format!("{violation:?}")}),
        )),
    }
}

async fn run_preflight(
    State(pool): State<ConnPool>,
    Path(task_id): Path<i64>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let result = crate::preflight::run_preflight(&conn, task_id);
    ok(json!(result))
}

#[derive(Deserialize)]
struct CommitMatchReq {
    commit_hash: String,
    commit_message: String,
}

async fn match_commit(
    State(pool): State<ConnPool>,
    Json(r): Json<CommitMatchReq>,
) -> impl IntoResponse {
    let conn = pool.get().map_err(|e| err(e))?;
    let matched = crate::workflow::match_commit_to_task(&conn, &r.commit_hash, &r.commit_message);
    ok(json!({"matched_tasks": matched}))
}

fn err(e: impl std::fmt::Display) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, e.to_string())
}

fn ok(v: serde_json::Value) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    Ok(Json(v))
}

fn ok_created(
    v: serde_json::Value,
) -> Result<(StatusCode, Json<serde_json::Value>), (StatusCode, String)> {
    Ok((StatusCode::CREATED, Json(v)))
}
