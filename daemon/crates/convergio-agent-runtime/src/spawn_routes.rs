//! HTTP endpoint for real agent spawning.
//!
//! POST /api/agents/spawn — creates worktree, writes instructions, launches process.

use std::sync::Arc;

use axum::extract::State;
use axum::response::Json;
use axum::routing::post;
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::spawner;
use crate::types::SpawnRequest;

pub struct SpawnState {
    pub pool: ConnPool,
    pub repo_root: String,
    pub daemon_url: String,
}

pub fn spawn_routes(state: Arc<SpawnState>) -> Router {
    Router::new()
        .route("/api/agents/spawn", post(handle_spawn))
        .with_state(state)
}

#[derive(Deserialize)]
struct SpawnBody {
    agent_name: String,
    org_id: String,
    task_id: Option<i64>,
    #[serde(default)]
    instructions: String,
    /// Model override (e.g. "claude-opus-4-6"). If None, uses tier default.
    model: Option<String>,
    /// Model tier: t1 (opus), t2 (sonnet), t3 (haiku), t4 (local).
    #[serde(default = "default_tier")]
    tier: String,
    #[serde(default = "default_budget")]
    budget_usd: f64,
    #[serde(default = "default_timeout")]
    timeout_secs: u64,
    #[serde(default)]
    priority: i32,
}

fn default_tier() -> String {
    "t2".into()
}
fn default_budget() -> f64 {
    10.0
}
fn default_timeout() -> u64 {
    7200
}

async fn handle_spawn(
    State(state): State<Arc<SpawnState>>,
    Json(body): Json<SpawnBody>,
) -> Json<Value> {
    let repo_root = std::path::Path::new(&state.repo_root);
    let wt_name = format!("agent-{}", &body.agent_name);

    // 1. Register in DB
    let agent_id = {
        let conn = match state.pool.get() {
            Ok(c) => c,
            Err(e) => return Json(json!({"error": e.to_string()})),
        };
        let hostname = gethostname();
        let req = SpawnRequest {
            agent_name: body.agent_name.clone(),
            org_id: body.org_id.clone(),
            task_id: body.task_id,
            capabilities: vec![],
            model_preference: body.model.clone(),
            budget_usd: body.budget_usd,
            priority: body.priority,
        };
        match crate::allocator::spawn(&conn, &req, &hostname) {
            Ok(id) => id,
            Err(e) => return Json(json!({"error": format!("allocator: {e}")})),
        }
    };

    // 2. Create worktree
    let workspace = match spawner::create_worktree(repo_root, &wt_name) {
        Ok(p) => p,
        Err(e) => return Json(json!({"error": format!("worktree: {e}"), "agent_id": agent_id})),
    };

    // 3. Write instructions
    if let Err(e) = spawner::write_instructions(&workspace, &body.instructions) {
        return Json(json!({"error": format!("instructions: {e}"), "agent_id": agent_id}));
    }

    // 4. Choose backend via tier
    let backend = spawner::backend_for_tier(&body.tier, body.model.as_deref());

    // 5. Spawn process
    let env_vars = [
        ("CONVERGIO_AGENT_NAME", body.agent_name.as_str()),
        ("CONVERGIO_ORG", body.org_id.as_str()),
        (
            "CONVERGIO_TASK_ID",
            &body.task_id.map(|id| id.to_string()).unwrap_or_default(),
        ),
        ("CONVERGIO_DAEMON_URL", state.daemon_url.as_str()),
        ("CONVERGIO_AGENT_ID", agent_id.as_str()),
    ];
    let result = spawner::spawn_process(&workspace, &backend, &env_vars, body.timeout_secs);

    match result {
        Ok(spawned) => {
            // 6. Activate agent in DB
            if let Ok(conn) = state.pool.get() {
                let _ = crate::allocator::activate(&conn, &agent_id);
                // Store PID for reaper
                let _ = conn.execute(
                    "UPDATE art_agents SET workspace_path = ?1 WHERE id = ?2",
                    rusqlite::params![workspace.to_string_lossy().as_ref(), agent_id],
                );
            }
            // 7. Start monitor — watches process, handles push/PR on completion
            crate::spawn_monitor::monitor_agent(
                state.pool.clone(),
                agent_id.clone(),
                spawned.pid,
                workspace.to_string_lossy().to_string(),
                state.repo_root.clone(),
            );
            tracing::info!(
                agent_id = agent_id.as_str(),
                pid = spawned.pid,
                backend = spawned.backend.as_str(),
                workspace = %workspace.display(),
                "agent process spawned + monitor attached"
            );
            Json(json!({
                "ok": true,
                "agent_id": agent_id,
                "pid": spawned.pid,
                "backend": spawned.backend,
                "workspace": workspace.to_string_lossy(),
            }))
        }
        Err(e) => {
            tracing::error!(agent_id = agent_id.as_str(), "spawn failed: {e}");
            Json(json!({"error": format!("spawn: {e}"), "agent_id": agent_id}))
        }
    }
}

fn gethostname() -> String {
    hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_else(|_| "unknown".into())
}
