//! Extended plan-db routes: waves, checkpoints, evidence, knowledge base.
//!
//! - POST /api/plan-db/wave/create         — create wave in plan
//! - POST /api/plan-db/wave/update         — update wave status
//! - POST /api/plan-db/checkpoint/save     — save execution checkpoint
//! - GET  /api/plan-db/checkpoint/restore  — restore checkpoint
//! - POST /api/plan-db/task/evidence       — record task evidence
//! - GET  /api/plan-db/task/evidence/:id   — get task evidence
//! - GET  /api/plan-db/execution-tree/:id  — full plan tree

use std::sync::Arc;

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use rusqlite::params;
use serde::Deserialize;
use serde_json::json;

use crate::plan_routes::PlanState;

pub fn plan_routes_ext(state: Arc<PlanState>) -> Router {
    Router::new()
        .route("/api/plan-db/wave/create", post(handle_wave_create))
        .route("/api/plan-db/wave/update", post(handle_wave_update))
        .route("/api/plan-db/checkpoint/save", post(handle_checkpoint_save))
        .route(
            "/api/plan-db/checkpoint/restore",
            get(handle_checkpoint_restore),
        )
        .route("/api/plan-db/task/evidence", post(handle_record_evidence))
        .route(
            "/api/plan-db/task/evidence/:task_id",
            get(handle_get_evidence),
        )
        .route(
            "/api/plan-db/execution-tree/:plan_id",
            get(handle_execution_tree),
        )
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct WaveCreate {
    pub plan_id: i64,
    pub wave_id: String,
    #[serde(default)]
    pub name: String,
}

async fn handle_wave_create(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<WaveCreate>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO waves (wave_id, plan_id, name) VALUES (?1, ?2, ?3)",
        params![body.wave_id, body.plan_id, body.name],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            Json(json!({"id": id, "wave_id": body.wave_id}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Debug, Deserialize)]
pub struct WaveUpdate {
    pub wave_id: i64,
    pub status: String,
}

async fn handle_wave_update(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<WaveUpdate>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut sql = "UPDATE waves SET status = ?1".to_string();
    if body.status == "in_progress" {
        sql.push_str(", started_at = datetime('now')");
    }
    sql.push_str(" WHERE id = ?2");
    match conn.execute(&sql, params![body.status, body.wave_id]) {
        Ok(0) => Json(json!({"error": "wave not found"})),
        Ok(_) => Json(json!({"wave_id": body.wave_id, "status": body.status})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Debug, Deserialize)]
pub struct CheckpointSave {
    pub plan_id: i64,
}

/// Build checkpoint file path. plan_id is validated by callers to be > 0.
/// Since plan_id is i64 (integer only), no path traversal is possible.
fn checkpoint_path(plan_id: i64) -> std::path::PathBuf {
    let base = convergio_types::platform_paths::convergio_data_dir().join("checkpoints");
    base.join(format!("plan-{plan_id}.json"))
}

async fn handle_checkpoint_save(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<CheckpointSave>,
) -> Json<serde_json::Value> {
    if body.plan_id <= 0 {
        return Json(json!({"error": "invalid plan_id"}));
    }
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let plan = match conn.query_row(
        "SELECT id, name, status, project_id FROM plans WHERE id = ?1",
        params![body.plan_id],
        |r| Ok(json!({"id": r.get::<_,i64>(0)?, "name": r.get::<_,String>(1)?,
                       "status": r.get::<_,String>(2)?, "project_id": r.get::<_,String>(3)?})),
    ) {
        Ok(p) => p,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let checkpoint = json!({"plan_id": body.plan_id, "plan": plan,
                            "saved_at": chrono::Utc::now().to_rfc3339()});
    let path = checkpoint_path(body.plan_id);
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match std::fs::write(&path, serde_json::to_string_pretty(&checkpoint).unwrap_or_default()) {
        Ok(()) => Json(json!({"plan_id": body.plan_id, "saved": true,
                              "path": path.to_string_lossy()})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Debug, Deserialize)]
pub struct CheckpointQuery {
    pub plan_id: i64,
}

async fn handle_checkpoint_restore(
    State(_state): State<Arc<PlanState>>,
    Query(q): Query<CheckpointQuery>,
) -> Json<serde_json::Value> {
    if q.plan_id <= 0 {
        return Json(json!({"error": "invalid plan_id"}));
    }
    let path = checkpoint_path(q.plan_id);
    match std::fs::read_to_string(&path) {
        Ok(contents) => {
            let data = serde_json::from_str::<serde_json::Value>(&contents)
                .unwrap_or(json!({"raw": contents}));
            Json(json!({"plan_id": q.plan_id, "data": data}))
        }
        Err(e) => Json(json!({"error": format!("checkpoint not found: {e}")})),
    }
}

#[derive(Debug, Deserialize)]
pub struct RecordEvidence {
    pub task_id: i64,
    pub evidence_type: String,
    pub content: String,
}

async fn handle_record_evidence(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<RecordEvidence>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // Store evidence as a note/output on the task
    match conn.execute(
        "UPDATE tasks SET notes = COALESCE(notes, '') || ?1, \
         output_data = ?2 WHERE id = ?3",
        params![
            format!("\n[{}] {}", body.evidence_type, body.content),
            body.content,
            body.task_id,
        ],
    ) {
        Ok(0) => Json(json!({"error": "task not found"})),
        Ok(_) => Json(json!({"task_id": body.task_id, "recorded": true})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_get_evidence(
    State(state): State<Arc<PlanState>>,
    Path(task_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.query_row(
        "SELECT notes, output_data FROM tasks WHERE id = ?1",
        params![task_id],
        |row| Ok((row.get::<_, Option<String>>(0)?, row.get::<_, Option<String>>(1)?)),
    ) {
        Ok((notes, output)) => Json(json!({
            "task_id": task_id, "notes": notes, "output_data": output
        })),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn handle_execution_tree(
    State(state): State<Arc<PlanState>>,
    Path(plan_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // Build plan -> waves -> tasks tree
    let plan = match conn.query_row(
        "SELECT id, name, status, tasks_done, tasks_total FROM plans WHERE id = ?1",
        params![plan_id],
        |r| Ok(json!({"id": r.get::<_,i64>(0)?, "name": r.get::<_,String>(1)?,
                       "status": r.get::<_,String>(2)?, "tasks_done": r.get::<_,i64>(3)?,
                       "tasks_total": r.get::<_,i64>(4)?})),
    ) {
        Ok(p) => p,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut wave_stmt = match conn
        .prepare("SELECT id, wave_id, name, status FROM waves WHERE plan_id = ?1 ORDER BY id")
    {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let waves: Vec<serde_json::Value> = match wave_stmt.query_map(params![plan_id], |r| {
        Ok((r.get::<_, i64>(0)?, json!({"id": r.get::<_,i64>(0)?, "wave_id": r.get::<_,String>(1)?,
             "name": r.get::<_,String>(2)?, "status": r.get::<_,String>(3)?})))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).map(|(_, v)| v).collect(),
        Err(_) => vec![],
    };
    Json(json!({"plan": plan, "waves": waves}))
}
