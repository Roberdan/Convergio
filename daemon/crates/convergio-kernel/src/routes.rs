//! HTTP API routes for convergio-kernel.
//!
//! - GET  /api/kernel/status     — engine status
//! - POST /api/kernel/classify   — classify a situation
//! - POST /api/kernel/ask        — route inference (local vs cloud)
//! - POST /api/kernel/verify     — verify task evidence
//! - GET  /api/kernel/events     — recent kernel events
//! - GET  /api/kernel/config     — read kernel config

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};
use tokio::sync::RwLock;

use crate::engine::KernelEngine;

pub struct KernelState {
    pub pool: ConnPool,
    pub engine: RwLock<KernelEngine>,
}

pub fn kernel_routes(state: Arc<KernelState>) -> Router {
    Router::new()
        .route("/api/kernel/status", get(handle_status))
        .route("/api/kernel/classify", post(handle_classify))
        .route("/api/kernel/ask", post(handle_ask))
        .route("/api/kernel/verify", post(handle_verify))
        .route("/api/kernel/events", get(handle_events))
        .route("/api/kernel/config", get(handle_config))
        .with_state(state)
}

async fn handle_status(State(s): State<Arc<KernelState>>) -> Json<Value> {
    let engine = s.engine.read().await;
    let status = engine.status();
    Json(json!({
        "models_loaded": status.models_loaded,
        "ram_gb": status.ram_gb,
        "uptime_secs": status.uptime_secs,
        "active_node": status.active_node,
        "last_check": status.last_check,
    }))
}

#[derive(Deserialize)]
struct ClassifyBody {
    situation: String,
}

async fn handle_classify(
    State(s): State<Arc<KernelState>>,
    Json(body): Json<ClassifyBody>,
) -> Json<Value> {
    let engine = s.engine.read().await;
    let action = engine.classify(&body.situation);
    // Log event to kernel_events
    if let Ok(conn) = s.pool.get() {
        let severity_str = format!("{}", action.severity);
        let _ = conn.execute(
            "INSERT INTO kernel_events (severity, source, message, action_taken) \
             VALUES (?1, 'classify', ?2, ?3)",
            rusqlite::params![severity_str, body.situation, action.action],
        );
    }
    Json(json!({
        "severity": format!("{}", action.severity),
        "action": action.action,
        "reason": action.reason,
    }))
}

#[derive(Deserialize)]
struct AskBody {
    query: String,
}

async fn handle_ask(State(s): State<Arc<KernelState>>, Json(body): Json<AskBody>) -> Json<Value> {
    let engine = s.engine.read().await;
    let level = engine.route_inference(&body.query);
    Json(json!({
        "level": format!("{:?}", level),
        "query_length": body.query.len(),
    }))
}

#[derive(Deserialize)]
struct VerifyBody {
    task_id: i64,
    status_requested: String,
    #[serde(default)]
    worktree: Option<String>,
    #[serde(default)]
    declared_outputs: Vec<String>,
}

async fn handle_verify(
    State(s): State<Arc<KernelState>>,
    Json(body): Json<VerifyBody>,
) -> Json<Value> {
    let report = crate::verify::verify_task(
        body.task_id,
        &body.status_requested,
        body.worktree.as_deref(),
        &body.declared_outputs,
    );
    // Log verification to kernel_verifications
    if let Ok(conn) = s.pool.get() {
        let checks_json = serde_json::to_string(&report.checks).unwrap_or_default();
        let _ = conn.execute(
            "INSERT INTO kernel_verifications \
             (task_id, checks_json, passed, blocked_reason) \
             VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![
                body.task_id,
                checks_json,
                report.passed as i32,
                if report.passed {
                    None::<String>
                } else {
                    Some(report.reason.clone())
                },
            ],
        );
    }
    Json(json!({
        "task_id": report.task_id,
        "passed": report.passed,
        "severity": format!("{}", report.severity),
        "action": report.action,
        "reason": report.reason,
        "checks": report.checks,
    }))
}

#[derive(Deserialize, Default)]
struct EventsQuery {
    limit: Option<u32>,
    severity: Option<String>,
}

async fn handle_events(
    State(s): State<Arc<KernelState>>,
    Query(q): Query<EventsQuery>,
) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let limit = q.limit.unwrap_or(50).min(200);
    let (sql, params): (String, Vec<Box<dyn rusqlite::types::ToSql>>) = match &q.severity {
        Some(sev) => (
            format!(
                "SELECT id, timestamp, severity, source, message, action_taken \
                 FROM kernel_events WHERE severity = ?1 \
                 ORDER BY timestamp DESC LIMIT {limit}"
            ),
            vec![Box::new(sev.clone())],
        ),
        None => (
            format!(
                "SELECT id, timestamp, severity, source, message, action_taken \
                 FROM kernel_events ORDER BY timestamp DESC LIMIT {limit}"
            ),
            vec![],
        ),
    };
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    let mut stmt = match conn.prepare(&sql) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map(param_refs.as_slice(), |r| {
        Ok(json!({
            "id": r.get::<_, i64>(0)?,
            "timestamp": r.get::<_, Option<String>>(1)?,
            "severity": r.get::<_, String>(2)?,
            "source": r.get::<_, Option<String>>(3)?,
            "message": r.get::<_, Option<String>>(4)?,
            "action_taken": r.get::<_, Option<String>>(5)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"events": rows}))
}

async fn handle_config(State(s): State<Arc<KernelState>>) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare("SELECT key, value, updated_at FROM kernel_config") {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map([], |r| {
        Ok(json!({
            "key": r.get::<_, String>(0)?,
            "value": r.get::<_, Option<String>>(1)?,
            "updated_at": r.get::<_, Option<String>>(2)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"config": rows}))
}
