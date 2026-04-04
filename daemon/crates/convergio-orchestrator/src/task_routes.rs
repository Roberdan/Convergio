//! HTTP route for task updates.

use std::sync::Arc;

use axum::extract::State;
use axum::response::Json;
use axum::routing::post;
use axum::Router;
use serde::Deserialize;
use serde_json::json;

use crate::plan_routes::PlanState;

pub fn task_routes(state: Arc<PlanState>) -> Router {
    Router::new()
        .route("/api/plan-db/task/update", post(handle_task_update))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct TaskUpdate {
    pub task_id: i64,
    #[serde(default)]
    pub status: Option<String>,
    #[serde(default)]
    pub notes: Option<String>,
    #[serde(default)]
    pub output_data: Option<String>,
    #[serde(default)]
    pub executor_agent: Option<String>,
    #[serde(default)]
    pub tokens: Option<i64>,
}

async fn handle_task_update(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<TaskUpdate>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut sets: Vec<String> = Vec::new();
    let mut p: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    if let Some(ref s) = body.status {
        p.push(Box::new(s.clone()));
        sets.push(format!("status = ?{}", p.len()));
        if s == "in_progress" {
            sets.push("started_at = datetime('now')".into());
        } else if s == "done" || s == "submitted" {
            sets.push("completed_at = datetime('now')".into());
        }
    }
    if let Some(ref n) = body.notes {
        p.push(Box::new(n.clone()));
        sets.push(format!("notes = ?{}", p.len()));
    }
    if let Some(ref o) = body.output_data {
        p.push(Box::new(o.clone()));
        sets.push(format!("output_data = ?{}", p.len()));
    }
    if let Some(ref a) = body.executor_agent {
        p.push(Box::new(a.clone()));
        sets.push(format!("executor_agent = ?{}", p.len()));
    }
    if let Some(t) = body.tokens {
        p.push(Box::new(t));
        sets.push(format!("tokens = ?{}", p.len()));
    }
    if sets.is_empty() {
        return Json(json!({"error": "no fields to update"}));
    }
    p.push(Box::new(body.task_id));
    let sql = format!(
        "UPDATE tasks SET {} WHERE id = ?{}",
        sets.join(", "),
        p.len()
    );
    let refs: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|v| v.as_ref()).collect();
    match conn.execute(&sql, refs.as_slice()) {
        Ok(0) => Json(json!({"error": "task not found"})),
        Ok(_) => Json(json!({"task_id": body.task_id, "updated": true})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}
