// HTTP routes for human-in-the-loop approval gates.
// WHY: Exposes approval workflow over REST so CLI, UI, and agents
// can request, grant, or reject approvals before critical operations.

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::approval;

pub fn approval_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/approvals/request", post(handle_request))
        .route("/api/approvals/pending", get(handle_pending))
        .route("/api/approvals/threshold", post(handle_set_threshold))
        .route("/api/approvals/check", get(handle_check))
        .route("/api/approvals/:id", get(handle_get))
        .route("/api/approvals/:id/approve", post(handle_approve))
        .route("/api/approvals/:id/reject", post(handle_reject))
        .with_state(pool)
}

#[derive(Deserialize)]
struct RequestBody {
    plan_id: i64,
    task_id: Option<i64>,
    approval_type: String,
    requester: String,
    #[serde(default)]
    reason: String,
}

async fn handle_request(State(pool): State<ConnPool>, Json(b): Json<RequestBody>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match approval::create_approval(
        &conn,
        b.plan_id,
        b.task_id,
        &b.approval_type,
        &b.requester,
        &b.reason,
    ) {
        Ok(id) => Json(json!({"ok": true, "id": id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct ApproveBody {
    reviewer: String,
}

async fn handle_approve(
    State(pool): State<ConnPool>,
    Path(id): Path<i64>,
    Json(b): Json<ApproveBody>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match approval::approve(&conn, id, &b.reviewer) {
        Ok(()) => Json(json!({"ok": true, "id": id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct RejectBody {
    reviewer: String,
    #[serde(default)]
    reason: String,
}

async fn handle_reject(
    State(pool): State<ConnPool>,
    Path(id): Path<i64>,
    Json(b): Json<RejectBody>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match approval::reject(&conn, id, &b.reviewer, &b.reason) {
        Ok(()) => Json(json!({"ok": true, "id": id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_pending(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let pending = approval::list_pending(&conn);
    Json(json!({"approvals": pending}))
}

async fn handle_get(State(pool): State<ConnPool>, Path(id): Path<i64>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match approval::get_approval(&conn, id) {
        Some(req) => Json(json!({"approval": req})),
        None => Json(json!({"error": "approval not found"})),
    }
}

#[derive(Deserialize)]
struct ThresholdBody {
    trigger: String,
    threshold_value: f64,
    #[serde(default)]
    auto_approve_below: f64,
}

async fn handle_set_threshold(
    State(pool): State<ConnPool>,
    Json(b): Json<ThresholdBody>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match approval::set_threshold(&conn, &b.trigger, b.threshold_value, b.auto_approve_below) {
        Ok(()) => Json(json!({"ok": true})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct CheckQuery {
    trigger: String,
    value: f64,
}

async fn handle_check(State(pool): State<ConnPool>, Query(q): Query<CheckQuery>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let needs_approval = approval::check_threshold(&conn, &q.trigger, q.value);
    Json(json!({"needs_approval": needs_approval, "trigger": q.trigger, "value": q.value}))
}
