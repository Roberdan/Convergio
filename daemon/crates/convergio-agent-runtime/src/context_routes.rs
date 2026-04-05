//! HTTP endpoints for per-agent context CRUD.

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::response::Json;
use axum::routing::{delete, get, post, put};
use axum::Router;
use convergio_db::pool::ConnPool;
use rusqlite::params;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::context;

/// Shared state for context routes.
pub struct ContextState {
    pub pool: ConnPool,
}

/// Build the context API router.
pub fn context_routes(state: Arc<ContextState>) -> Router {
    Router::new()
        .route("/api/agents/:id/context", get(handle_list))
        .route("/api/agents/:id/context/seed", post(handle_seed))
        .route("/api/agents/:id/context/:key", get(handle_get))
        .route("/api/agents/:id/context/:key", put(handle_set))
        .route("/api/agents/:id/context/:key", delete(handle_delete))
        .with_state(state)
}

async fn handle_list(
    State(state): State<Arc<ContextState>>,
    Path(agent_id): Path<String>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    match context::list(&conn, &agent_id) {
        Ok(entries) => Json(json!({ "entries": entries })),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

async fn handle_get(
    State(state): State<Arc<ContextState>>,
    Path((agent_id, key)): Path<(String, String)>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    match context::get(&conn, &agent_id, &key) {
        Ok(Some(entry)) => Json(json!(entry)),
        Ok(None) => err_json("NOT_FOUND", "context key not found"),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

#[derive(Deserialize)]
struct SetBody {
    value: String,
    #[serde(default = "default_set_by")]
    set_by: String,
}

fn default_set_by() -> String {
    "agent".into()
}

async fn handle_set(
    State(state): State<Arc<ContextState>>,
    Path((agent_id, key)): Path<(String, String)>,
    Json(body): Json<SetBody>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    match context::set(&conn, &agent_id, &key, &body.value, &body.set_by) {
        Ok(entry) => Json(json!(entry)),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

async fn handle_delete(
    State(state): State<Arc<ContextState>>,
    Path((agent_id, key)): Path<(String, String)>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    match context::delete(&conn, &agent_id, &key) {
        Ok(true) => Json(json!({ "deleted": true })),
        Ok(false) => err_json("NOT_FOUND", "context key not found"),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

async fn handle_seed(
    State(state): State<Arc<ContextState>>,
    Path(agent_id): Path<String>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    // Look up task_id and org_id from art_agents
    let agent_row: Result<(Option<i64>, String), _> = conn.query_row(
        "SELECT task_id, org_id FROM art_agents WHERE id = ?1",
        params![agent_id],
        |r| Ok((r.get(0)?, r.get(1)?)),
    );
    let (task_id, org_id) = match agent_row {
        Ok(row) => row,
        Err(rusqlite::Error::QueryReturnedNoRows) => {
            return err_json("NOT_FOUND", "agent not found");
        }
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    match context::seed(&conn, &agent_id, task_id, &org_id) {
        Ok(count) => Json(json!({ "seeded": count })),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

fn err_json(code: &str, message: &str) -> Json<Value> {
    Json(json!({ "error": { "code": code, "message": message } }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_context_routes_builds() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let state = Arc::new(ContextState { pool });
        let _router = context_routes(state);
    }
}
