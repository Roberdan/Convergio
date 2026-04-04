//! HTTP routes for file transport operations.

use axum::extract::{Path, Query, State};
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::types::{TransferDirection, TransferRequest};

/// Query parameters for listing transfers.
#[derive(Deserialize)]
pub struct ListParams {
    pub peer: Option<String>,
    pub limit: Option<u32>,
}

/// Build the file-transport router.
pub fn file_transport_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/file-transport/push", post(push_transfer))
        .route("/api/file-transport/pull", post(pull_transfer))
        .route("/api/file-transport/transfers", get(list_transfers))
        .route("/api/file-transport/transfers/:id", get(get_transfer))
        .with_state(pool)
}

async fn push_transfer(
    State(pool): State<ConnPool>,
    Json(mut req): Json<TransferRequest>,
) -> Json<Value> {
    req.direction = TransferDirection::Push;
    execute_and_record(pool, req).await
}

async fn pull_transfer(
    State(pool): State<ConnPool>,
    Json(mut req): Json<TransferRequest>,
) -> Json<Value> {
    req.direction = TransferDirection::Pull;
    execute_and_record(pool, req).await
}

async fn execute_and_record(pool: ConnPool, req: TransferRequest) -> Json<Value> {
    let result = match crate::rsync::execute_rsync(&req, &req.ssh_target).await {
        Ok(r) => r,
        Err(e) => {
            return Json(json!({"ok": false, "error": e.to_string()}));
        }
    };

    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            // Transfer ran but we couldn't record it
            return Json(json!({
                "ok": true,
                "result": result,
                "warning": format!("transfer completed but recording failed: {e}"),
            }));
        }
    };

    match crate::transfer::record_transfer(&conn, &result, &req) {
        Ok(id) => Json(json!({"ok": true, "id": id, "result": result})),
        Err(e) => Json(json!({
            "ok": true,
            "result": result,
            "warning": format!("transfer completed but recording failed: {e}"),
        })),
    }
}

async fn list_transfers(
    State(pool): State<ConnPool>,
    Query(params): Query<ListParams>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    let limit = params.limit.unwrap_or(50).min(100);
    match crate::transfer::list_transfers(&conn, params.peer.as_deref(), limit) {
        Ok(list) => Json(json!({"ok": true, "transfers": list})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

async fn get_transfer(State(pool): State<ConnPool>, Path(id): Path<i64>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    match crate::transfer::get_transfer(&conn, id) {
        Ok(Some(rec)) => Json(json!({"ok": true, "transfer": rec})),
        Ok(None) => Json(json!({"ok": false, "error": "transfer not found"})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}
