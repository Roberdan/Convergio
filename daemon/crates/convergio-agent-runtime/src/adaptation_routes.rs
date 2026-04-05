//! HTTP endpoints for agent live adaptation.
//!
//! - GET  /api/agents/:id/updates?since=...  — poll all updates
//! - POST /api/agents/:id/sentinel/:name     — write sentinel
//! - DELETE /api/agents/:id/sentinel/:name   — clear sentinel

use std::sync::Arc;

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{delete, get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use rusqlite::params;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::adaptation;

/// Shared state for adaptation routes.
pub struct AdaptationState {
    pub pool: ConnPool,
}

#[derive(Deserialize)]
pub struct UpdatesQuery {
    since: Option<String>,
}

/// Build the adaptation API router.
pub fn adaptation_routes(state: Arc<AdaptationState>) -> Router {
    Router::new()
        .route("/api/agents/:id/updates", get(handle_poll_updates))
        .route("/api/agents/:id/sentinel/:name", post(handle_write))
        .route("/api/agents/:id/sentinel/:name", delete(handle_clear))
        .with_state(state)
}

async fn handle_poll_updates(
    State(state): State<Arc<AdaptationState>>,
    Path(agent_id): Path<String>,
    Query(q): Query<UpdatesQuery>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    let since = q.since.as_deref().unwrap_or("1970-01-01");
    match adaptation::poll_updates(&conn, &agent_id, since) {
        Ok(updates) => Json(json!(updates)),
        Err(crate::types::RuntimeError::NotFound(_)) => err_json("NOT_FOUND", "agent not found"),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

async fn handle_write(
    State(state): State<Arc<AdaptationState>>,
    Path((agent_id, name)): Path<(String, String)>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    let ws = match lookup_workspace(&conn, &agent_id) {
        Ok(w) => w,
        Err(resp) => return resp,
    };
    match adaptation::write_sentinel(&ws, &name) {
        Ok(()) => Json(json!({ "ok": true, "sentinel": name })),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

async fn handle_clear(
    State(state): State<Arc<AdaptationState>>,
    Path((agent_id, name)): Path<(String, String)>,
) -> Json<Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return err_json("INTERNAL", &e.to_string()),
    };
    let ws = match lookup_workspace(&conn, &agent_id) {
        Ok(w) => w,
        Err(resp) => return resp,
    };
    match adaptation::clear_sentinel(&ws, &name) {
        Ok(()) => Json(json!({ "ok": true, "cleared": name })),
        Err(e) => err_json("INTERNAL", &e.to_string()),
    }
}

fn lookup_workspace(conn: &rusqlite::Connection, agent_id: &str) -> Result<String, Json<Value>> {
    let row: Result<Option<String>, _> = conn.query_row(
        "SELECT workspace_path FROM art_agents WHERE id = ?1",
        params![agent_id],
        |r| r.get(0),
    );
    match row {
        Ok(Some(ws)) => Ok(ws),
        Ok(None) => Err(err_json("BAD_REQUEST", "agent has no workspace")),
        Err(rusqlite::Error::QueryReturnedNoRows) => Err(err_json("NOT_FOUND", "agent not found")),
        Err(e) => Err(err_json("INTERNAL", &e.to_string())),
    }
}

fn err_json(code: &str, message: &str) -> Json<Value> {
    Json(json!({ "error": { "code": code, "message": message } }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_adaptation_routes_builds() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let state = Arc::new(AdaptationState { pool });
        let _router = adaptation_routes(state);
    }
}
