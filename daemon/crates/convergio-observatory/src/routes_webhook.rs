//! Webhook and export route handlers for the observatory.

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde::Deserialize;

use crate::export;
use crate::routes::ObservatoryState;

pub(crate) async fn handle_metrics(State(state): State<Arc<ObservatoryState>>) -> Response {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return "# error: pool unavailable\n".into_response(),
    };
    match export::prometheus_exposition(&conn) {
        Ok(text) => (
            [(
                axum::http::header::CONTENT_TYPE,
                "text/plain; version=0.0.4; charset=utf-8",
            )],
            text,
        )
            .into_response(),
        Err(_) => "# error: query failed\n".into_response(),
    }
}

#[derive(Debug, Deserialize)]
pub struct WebhookRequest {
    pub url: String,
    pub event_filter: Option<String>,
}

pub(crate) async fn handle_register_webhook(
    State(state): State<Arc<ObservatoryState>>,
    Json(body): Json<WebhookRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(super::routes::err_json("POOL_ERROR", &e.to_string())),
    };
    let filter = body.event_filter.as_deref().unwrap_or("*");
    match export::register_webhook(&conn, &body.url, filter) {
        Ok(id) => Json(serde_json::json!({ "ok": true, "id": id })),
        Err(e) => Json(super::routes::err_json("DB_ERROR", &e.to_string())),
    }
}

pub(crate) async fn handle_list_webhooks(
    State(state): State<Arc<ObservatoryState>>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(super::routes::err_json("POOL_ERROR", &e.to_string())),
    };
    match export::list_webhooks(&conn) {
        Ok(hooks) => {
            let items: Vec<serde_json::Value> = hooks
                .into_iter()
                .map(|(id, url, ef)| serde_json::json!({"id": id, "url": url, "event_filter": ef}))
                .collect();
            Json(serde_json::json!({ "ok": true, "webhooks": items }))
        }
        Err(e) => Json(super::routes::err_json("QUERY_ERROR", &e.to_string())),
    }
}

pub(crate) async fn handle_remove_webhook(
    State(state): State<Arc<ObservatoryState>>,
    Path(id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(super::routes::err_json("POOL_ERROR", &e.to_string())),
    };
    match export::remove_webhook(&conn, id) {
        Ok(true) => Json(serde_json::json!({ "ok": true })),
        Ok(false) => Json(super::routes::err_json("NOT_FOUND", "webhook not found")),
        Err(e) => Json(super::routes::err_json("DB_ERROR", &e.to_string())),
    }
}
