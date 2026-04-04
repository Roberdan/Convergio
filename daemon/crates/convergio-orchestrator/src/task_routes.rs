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
        .route("/api/plan-db/task/create", post(handle_task_create))
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

#[derive(Debug, Deserialize)]
pub struct TaskCreate {
    pub plan_id: i64,
    pub wave_id: i64,
    pub title: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub task_id: Option<String>,
    #[serde(default)]
    pub executor_agent: Option<String>,
}

async fn handle_task_create(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<TaskCreate>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // ImportGate: only add tasks to plans in draft/todo/approved
    if let Err(gate_err) = crate::gates::import_gate(&conn, body.plan_id) {
        return Json(json!({"error": format!("gate blocked: {gate_err}")}));
    }
    let task_id_str = body
        .task_id
        .unwrap_or_else(|| format!("T-{}", body.plan_id));
    match conn.execute(
        "INSERT INTO tasks (task_id, plan_id, wave_id, title, description, executor_agent) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        rusqlite::params![
            task_id_str,
            body.plan_id,
            body.wave_id,
            body.title,
            body.description.as_deref().unwrap_or(""),
            body.executor_agent.as_deref().unwrap_or(""),
        ],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            // Update tasks_total on plan
            let _ = conn.execute(
                "UPDATE plans SET tasks_total = tasks_total + 1 WHERE id = ?1",
                rusqlite::params![body.plan_id],
            );
            Json(json!({"id": id, "task_id": task_id_str}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_task_update(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<TaskUpdate>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // Lifecycle gate check (24f): validate transition before applying
    if let Some(ref new_status) = body.status {
        if let Err(gate_err) =
            crate::gates::check_task_transition(&state.pool, body.task_id, new_status)
        {
            tracing::warn!(
                task_id = body.task_id,
                gate = gate_err.gate,
                "gate blocked transition"
            );
            return Json(
                json!({"error": format!("gate blocked: {gate_err}"), "gate": gate_err.gate}),
            );
        }
    }

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
        Ok(_) => {
            // Emit lifecycle events when task reaches a terminal status
            if let Some(ref new_status) = body.status {
                if new_status == "done" || new_status == "submitted" {
                    drop(conn);
                    emit_task_lifecycle(&state, body.task_id);
                }
            }
            Json(json!({"task_id": body.task_id, "updated": true}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

/// Emit IPC task_done (for reactor) and DomainEvent TaskCompleted (for SSE/UI).
/// Handles its own DB connection to avoid holding the pool during IPC emit.
fn emit_task_lifecycle(state: &PlanState, task_id: i64) {
    let plan_id = {
        let conn = match state.pool.get() {
            Ok(c) => c,
            Err(e) => {
                tracing::warn!(task_id, "pool error in emit_task_lifecycle: {e}");
                return;
            }
        };

        // Look up plan_id for this task
        let plan_id: Option<i64> = conn
            .query_row(
                "SELECT plan_id FROM tasks WHERE id = ?1",
                rusqlite::params![task_id],
                |row| row.get(0),
            )
            .ok();

        let Some(plan_id) = plan_id else {
            tracing::warn!(task_id, "task has no plan_id — skipping lifecycle emit");
            return;
        };

        // Increment tasks_done counter on plan
        let _ = conn.execute(
            "UPDATE plans SET tasks_done = tasks_done + 1, updated_at = datetime('now') \
             WHERE id = ?1",
            rusqlite::params![plan_id],
        );

        plan_id
        // conn dropped here — pool slot freed for IPC emit
    };

    // Emit IPC to #orchestration → triggers reactor chain.
    // Use "task-updater" as sender so the reactor (ali-orchestrator) processes it.
    // The reactor skips messages from itself to avoid loops.
    let content = json!({
        "type": "task_done",
        "task_id": task_id.to_string(),
        "plan_id": plan_id
    });
    if let Err(e) = convergio_ipc::messaging::broadcast(
        &state.pool,
        &state.notify,
        "task-updater",
        &content.to_string(),
        "event",
        Some("#orchestration"),
        100,
    ) {
        tracing::warn!(task_id, "failed to emit task_done IPC: {e}");
    }

    // Emit DomainEvent for SSE → UI
    if let Some(ref sink) = state.event_sink {
        sink.emit(convergio_types::events::make_event(
            "orchestrator",
            convergio_types::events::EventKind::TaskCompleted { task_id },
            convergio_types::events::EventContext {
                plan_id: Some(plan_id),
                task_id: Some(task_id),
                ..Default::default()
            },
        ));
    }

    tracing::info!(task_id, plan_id, "task lifecycle events emitted");
}

#[cfg(test)]
#[path = "task_routes_tests.rs"]
mod tests;
