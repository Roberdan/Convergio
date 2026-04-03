//! HTTP API routes for the observatory.
//!
//! - GET  /api/observatory/timeline     — event timeline with filters
//! - GET  /api/observatory/search       — full-text search
//! - GET  /api/observatory/dashboard    — aggregate dashboard data
//! - GET  /api/observatory/anomalies    — detected anomalies
//! - POST /api/observatory/anomalies/:id/resolve — resolve anomaly
//! - GET  /api/observatory/metrics      — Prometheus exposition
//! - GET  /api/observatory/webhooks     — list webhooks
//! - POST /api/observatory/webhooks     — register webhook
//! - DELETE /api/observatory/webhooks/:id — remove webhook

use std::sync::Arc;

use axum::extract::{Path, Query, State};
use axum::routing::{delete, get, post};
use axum::{Json, Router};
use serde::Deserialize;

use convergio_db::pool::ConnPool;

use crate::routes_webhook::{
    handle_list_webhooks, handle_metrics, handle_register_webhook, handle_remove_webhook,
};
use crate::timeline::TimelineFilter;
use crate::{anomaly, dashboard, search, timeline};

/// Shared state for observatory routes.
pub struct ObservatoryState {
    pub pool: ConnPool,
}

/// Build the observatory API router.
pub fn observatory_routes(state: Arc<ObservatoryState>) -> Router {
    Router::new()
        .route("/api/observatory/timeline", get(handle_timeline))
        .route("/api/observatory/search", get(handle_search))
        .route("/api/observatory/dashboard", get(handle_dashboard))
        .route("/api/observatory/anomalies", get(handle_anomalies))
        .route(
            "/api/observatory/anomalies/:id/resolve",
            post(handle_resolve),
        )
        .route("/api/observatory/metrics", get(handle_metrics))
        .route(
            "/api/observatory/webhooks",
            get(handle_list_webhooks).post(handle_register_webhook),
        )
        .route(
            "/api/observatory/webhooks/:id",
            delete(handle_remove_webhook),
        )
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct TimelineQuery {
    pub org_id: Option<String>,
    pub source: Option<String>,
    pub event_type: Option<String>,
    pub node_id: Option<String>,
    pub since: Option<String>,
    pub until: Option<String>,
    pub limit: Option<u32>,
}

async fn handle_timeline(
    State(state): State<Arc<ObservatoryState>>,
    Query(q): Query<TimelineQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let filter = TimelineFilter {
        org_id: q.org_id.as_deref(),
        source: q.source.as_deref(),
        event_type: q.event_type.as_deref(),
        node_id: q.node_id.as_deref(),
        since: q.since.as_deref(),
        until: q.until.as_deref(),
        limit: q.limit.unwrap_or(100),
    };
    match timeline::query_timeline(&conn, &filter) {
        Ok(events) => Json(serde_json::json!({ "ok": true, "events": events })),
        Err(e) => Json(err_json("QUERY_ERROR", &e.to_string())),
    }
}

#[derive(Debug, Deserialize)]
pub struct SearchQuery {
    pub q: String,
    pub limit: Option<u32>,
}

async fn handle_search(
    State(state): State<Arc<ObservatoryState>>,
    Query(q): Query<SearchQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    match search::search(&conn, &q.q, q.limit.unwrap_or(50)) {
        Ok(results) => Json(serde_json::json!({ "ok": true, "results": results })),
        Err(e) => Json(err_json("SEARCH_ERROR", &e.to_string())),
    }
}

#[derive(Debug, Deserialize)]
pub struct DashboardQuery {
    pub org_id: Option<String>,
    pub since: Option<String>,
    pub until: Option<String>,
}

async fn handle_dashboard(
    State(state): State<Arc<ObservatoryState>>,
    Query(q): Query<DashboardQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let since = q.since.as_deref().unwrap_or("2020-01-01");
    let until = q.until.as_deref().unwrap_or("2099-12-31");
    let costs = q
        .org_id
        .as_deref()
        .map(|oid| dashboard::cost_per_hour(&conn, oid, since, until).unwrap_or_default());
    let throughput =
        dashboard::task_throughput(&conn, q.org_id.as_deref(), since, until).unwrap_or_default();
    let latency = dashboard::model_latency(&conn).unwrap_or_default();
    Json(serde_json::json!({
        "ok": true,
        "cost_per_hour": costs,
        "task_throughput": throughput,
        "model_latency": latency,
    }))
}

#[derive(Debug, Deserialize)]
pub struct AnomalyQuery {
    pub kind: Option<String>,
    pub include_resolved: Option<bool>,
    pub limit: Option<u32>,
}

async fn handle_anomalies(
    State(state): State<Arc<ObservatoryState>>,
    Query(q): Query<AnomalyQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    let kind = q
        .kind
        .as_deref()
        .map(crate::types::AnomalyKind::from_str_value);
    let result = anomaly::list_anomalies(
        &conn,
        kind.as_ref(),
        q.include_resolved.unwrap_or(false),
        q.limit.unwrap_or(50),
    );
    match result {
        Ok(list) => Json(serde_json::json!({ "ok": true, "anomalies": list })),
        Err(e) => Json(err_json("QUERY_ERROR", &e.to_string())),
    }
}

async fn handle_resolve(
    State(state): State<Arc<ObservatoryState>>,
    Path(id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(err_json("POOL_ERROR", &e.to_string())),
    };
    match anomaly::resolve_anomaly(&conn, id) {
        Ok(true) => Json(serde_json::json!({ "ok": true })),
        Ok(false) => Json(err_json("NOT_FOUND", "anomaly not found")),
        Err(e) => Json(err_json("DB_ERROR", &e.to_string())),
    }
}

pub(crate) fn err_json(code: &str, message: &str) -> serde_json::Value {
    serde_json::json!({
        "error": { "code": code, "message": message }
    })
}
