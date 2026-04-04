// HTTP routes for artifact bundle management.
// WHY: Bundles group artifacts into reviewable deliverables with lifecycle
// tracking (draft -> reviewed -> published).

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::json;

use crate::artifact_bundle;

pub fn bundle_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/bundles/create", post(handle_create))
        .route("/api/bundles/:id/add", post(handle_add))
        .route("/api/bundles/plan/:plan_id", get(handle_list))
        .route("/api/bundles/:id", get(handle_get))
        .route("/api/bundles/:id/publish", post(handle_publish))
        .with_state(pool)
}

#[derive(Deserialize)]
struct CreateReq {
    plan_id: i64,
    name: String,
    bundle_type: Option<String>,
}

#[derive(Deserialize)]
struct AddReq {
    artifact_id: i64,
}

async fn handle_create(
    State(pool): State<ConnPool>,
    Json(req): Json<CreateReq>,
) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": e.to_string()})),
            )
        }
    };
    let btype = req.bundle_type.as_deref().unwrap_or("deliverable");
    match artifact_bundle::create_bundle(&conn, req.plan_id, &req.name, btype) {
        Ok(id) => (StatusCode::CREATED, Json(json!({"id": id}))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_add(
    State(pool): State<ConnPool>,
    Path(id): Path<i64>,
    Json(req): Json<AddReq>,
) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": e.to_string()})),
            )
        }
    };
    match artifact_bundle::add_to_bundle(&conn, id, req.artifact_id) {
        Ok(()) => (StatusCode::OK, Json(json!({"ok": true}))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_list(
    State(pool): State<ConnPool>,
    Path(plan_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    Json(json!(artifact_bundle::list_bundles(&conn, plan_id)))
}

async fn handle_get(State(pool): State<ConnPool>, Path(id): Path<i64>) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match artifact_bundle::get_bundle_with_artifacts(&conn, id) {
        Some((bundle, artifact_ids)) => {
            Json(json!({"bundle": bundle, "artifact_ids": artifact_ids}))
        }
        None => Json(json!({"error": "bundle not found"})),
    }
}

async fn handle_publish(State(pool): State<ConnPool>, Path(id): Path<i64>) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": e.to_string()})),
            )
        }
    };
    match artifact_bundle::update_bundle_status(&conn, id, "published") {
        Ok(()) => (StatusCode::OK, Json(json!({"ok": true}))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}
