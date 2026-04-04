// HTTP routes for compensation/rollback actions.
// WHY: Expose compensation triggers and queries so the CLI and reactor
// can manage wave failure recovery through the daemon API.

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::json;

use crate::compensation;

pub fn compensation_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/compensations/trigger", post(handle_trigger))
        .route("/api/compensations/plan/:plan_id", get(handle_list_by_plan))
        .route("/api/compensations/wave/:wave_id", get(handle_list_by_wave))
        .route("/api/compensations/:id/execute", post(handle_execute_one))
        .route(
            "/api/compensations/wave/:wave_id/execute-all",
            post(handle_execute_all),
        )
        .route("/api/compensations/:id", get(handle_get))
        .with_state(pool)
}

#[derive(Deserialize)]
struct TriggerReq {
    wave_id: i64,
    reason: String,
}

async fn handle_trigger(
    State(pool): State<ConnPool>,
    Json(req): Json<TriggerReq>,
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
    match compensation::build_compensation_plan(&conn, req.wave_id, &req.reason) {
        Ok(plan) => (StatusCode::CREATED, Json(json!({"plan": plan}))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_list_by_plan(
    State(pool): State<ConnPool>,
    Path(plan_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match compensation::list_compensations(&conn, plan_id) {
        Ok(actions) => Json(json!({"actions": actions})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_list_by_wave(
    State(pool): State<ConnPool>,
    Path(wave_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match compensation::get_wave_compensations(&conn, wave_id) {
        Ok(actions) => Json(json!({"actions": actions})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_execute_one(
    State(pool): State<ConnPool>,
    Path(id): Path<i64>,
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
    match compensation::execute_compensation(&conn, id) {
        Ok(()) => (StatusCode::OK, Json(json!({"ok": true}))),
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_execute_all(
    State(pool): State<ConnPool>,
    Path(wave_id): Path<i64>,
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
    match compensation::get_wave_compensations(&conn, wave_id) {
        Ok(actions) => {
            let pending: Vec<_> = actions.iter().filter(|a| a.status == "pending").collect();
            let mut executed = 0;
            for a in &pending {
                if compensation::execute_compensation(&conn, a.id).is_ok() {
                    executed += 1;
                }
            }
            (StatusCode::OK, Json(json!({"executed": executed})))
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_get(State(pool): State<ConnPool>, Path(id): Path<i64>) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match compensation::get_single(&conn, id) {
        Ok(action) => Json(json!({"action": action})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}
