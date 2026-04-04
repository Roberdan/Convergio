//! HTTP routes for plan-db CRUD operations.
//!
//! - GET  /api/plan-db/list         — list plans (optional ?status, ?project_id)
//! - POST /api/plan-db/create       — create a new plan
//! - GET  /api/plan-db/json/:id     — get plan with waves and tasks
//! - POST /api/plan-db/start/:id    — set plan status to in_progress
//! - POST /api/plan-db/complete/:id — set plan status to done
//! - POST /api/plan-db/cancel/:id   — set plan status to cancelled
//! - POST /api/plan-db/task/update  — update task status/notes/output

use std::sync::Arc;

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use rusqlite::params;
use serde::Deserialize;
use serde_json::json;

use convergio_db::pool::ConnPool;
use convergio_types::events::DomainEventSink;

pub struct PlanState {
    pub pool: ConnPool,
    pub event_sink: Option<Arc<dyn DomainEventSink>>,
    pub notify: Arc<tokio::sync::Notify>,
}

pub fn plan_routes(state: Arc<PlanState>) -> Router {
    Router::new()
        .route("/api/plan-db/list", get(handle_list))
        .route("/api/plan-db/create", post(handle_create))
        .route("/api/plan-db/json/:plan_id", get(handle_get))
        .route("/api/plan-db/start/:plan_id", post(handle_start))
        .route("/api/plan-db/complete/:plan_id", post(handle_complete))
        .route("/api/plan-db/cancel/:plan_id", post(handle_cancel))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct ListQuery {
    pub status: Option<String>,
    pub project_id: Option<String>,
}

async fn handle_list(
    State(state): State<Arc<PlanState>>,
    Query(q): Query<ListQuery>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut sql = "SELECT id, project_id, name, status, tasks_done, tasks_total, \
                   created_at, updated_at FROM plans"
        .to_string();
    let mut conds: Vec<String> = Vec::new();
    let mut p: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    if let Some(ref s) = q.status {
        p.push(Box::new(s.clone()));
        conds.push(format!("status = ?{}", p.len()));
    }
    if let Some(ref pid) = q.project_id {
        p.push(Box::new(pid.clone()));
        conds.push(format!("project_id = ?{}", p.len()));
    }
    if !conds.is_empty() {
        sql.push_str(&format!(" WHERE {}", conds.join(" AND ")));
    }
    sql.push_str(" ORDER BY id DESC LIMIT 100");
    let refs: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|v| v.as_ref()).collect();
    let mut stmt = match conn.prepare(&sql) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let plans: Vec<serde_json::Value> = match stmt.query_map(refs.as_slice(), |row| {
        Ok(json!({
            "id": row.get::<_, i64>(0)?,
            "project_id": row.get::<_, String>(1)?,
            "name": row.get::<_, String>(2)?,
            "status": row.get::<_, String>(3)?,
            "tasks_done": row.get::<_, i64>(4)?,
            "tasks_total": row.get::<_, i64>(5)?,
            "created_at": row.get::<_, String>(6)?,
            "updated_at": row.get::<_, String>(7)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    Json(json!(plans))
}

#[derive(Debug, Deserialize)]
pub struct CreatePlan {
    pub project_id: String,
    pub name: String,
    #[serde(default)]
    pub depends_on: Option<String>,
    #[serde(default)]
    pub execution_mode: Option<String>,
    #[serde(default)]
    pub tasks_total: i64,
    /// Protocol fields (24f): optional but logged if missing.
    pub objective: Option<String>,
    pub motivation: Option<String>,
    pub requester: Option<String>,
}

async fn handle_create(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<CreatePlan>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO plans (project_id, name, depends_on, execution_mode, tasks_total) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            body.project_id,
            body.name,
            body.depends_on,
            body.execution_mode,
            body.tasks_total
        ],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            if let Some(ref sink) = state.event_sink {
                sink.emit(convergio_types::events::make_event(
                    "orchestrator",
                    convergio_types::events::EventKind::PlanCreated {
                        plan_id: id,
                        name: body.name.clone(),
                    },
                    convergio_types::events::EventContext {
                        plan_id: Some(id),
                        ..Default::default()
                    },
                ));
            }
            // Auto-create plan_metadata if protocol fields provided (24f)
            if body.objective.is_some() || body.motivation.is_some() || body.requester.is_some() {
                let _ = conn.execute(
                    "INSERT OR IGNORE INTO plan_metadata (plan_id, objective, motivation, requester) \
                     VALUES (?1, ?2, ?3, ?4)",
                    params![id, body.objective, body.motivation, body.requester],
                );
            }
            Json(json!({"id": id, "status": "created"}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_get(
    State(state): State<Arc<PlanState>>,
    Path(plan_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let plan = conn.query_row(
        "SELECT id, project_id, name, status, tasks_done, tasks_total, \
         depends_on, execution_mode, created_at, updated_at FROM plans WHERE id = ?1",
        params![plan_id],
        |row| {
            Ok(json!({
                "id": row.get::<_, i64>(0)?,
                "project_id": row.get::<_, String>(1)?,
                "name": row.get::<_, String>(2)?,
                "status": row.get::<_, String>(3)?,
                "tasks_done": row.get::<_, i64>(4)?,
                "tasks_total": row.get::<_, i64>(5)?,
                "depends_on": row.get::<_, Option<String>>(6)?,
                "execution_mode": row.get::<_, Option<String>>(7)?,
                "created_at": row.get::<_, String>(8)?,
                "updated_at": row.get::<_, String>(9)?,
            }))
        },
    );
    match plan {
        Ok(p) => Json(p),
        Err(rusqlite::Error::QueryReturnedNoRows) => Json(json!({"error": "plan not found"})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

fn set_plan_status(pool: &ConnPool, plan_id: i64, status: &str) -> serde_json::Value {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return json!({"error": e.to_string()}),
    };
    match conn.execute(
        "UPDATE plans SET status = ?1, updated_at = datetime('now') WHERE id = ?2",
        params![status, plan_id],
    ) {
        Ok(0) => json!({"error": "plan not found"}),
        Ok(_) => json!({"id": plan_id, "status": status}),
        Err(e) => json!({"error": e.to_string()}),
    }
}

async fn handle_start(
    State(s): State<Arc<PlanState>>,
    Path(id): Path<i64>,
) -> Json<serde_json::Value> {
    Json(set_plan_status(&s.pool, id, "in_progress"))
}

async fn handle_complete(
    State(s): State<Arc<PlanState>>,
    Path(id): Path<i64>,
) -> Json<serde_json::Value> {
    Json(set_plan_status(&s.pool, id, "done"))
}

async fn handle_cancel(
    State(s): State<Arc<PlanState>>,
    Path(id): Path<i64>,
) -> Json<serde_json::Value> {
    Json(set_plan_status(&s.pool, id, "cancelled"))
}
