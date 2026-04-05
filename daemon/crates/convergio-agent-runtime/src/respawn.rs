//! Auto-respawn: when an agent exits with a checkpoint, spawn a continuation.
//!
//! The daemon detects that an agent stopped with a saved checkpoint and
//! remaining budget, then spawns a continuation that resumes the work.

use convergio_db::pool::ConnPool;
use rusqlite::params;

use crate::types::{RuntimeError, RuntimeResult};

/// Agent record needed for respawn decisions.
struct AgentRecord {
    agent_name: String,
    org_id: String,
    task_id: Option<i64>,
    model: Option<String>,
    budget: f64,
    spent: f64,
    respawn_count: i32,
    max_respawns: i32,
}

/// Check if an agent should be respawned and do it.
/// Returns the new agent_id if respawned, None if not.
pub fn try_respawn(
    pool: &ConnPool,
    agent_id: &str,
    daemon_url: &str,
    repo_root: &str,
) -> RuntimeResult<Option<String>> {
    let conn = pool.get()?;
    let rec = load_agent(&conn, agent_id)?;

    // Guard: respawn limit
    if rec.respawn_count >= rec.max_respawns {
        tracing::info!(agent_id, count = rec.respawn_count, "max respawns reached");
        return Ok(None);
    }

    // Guard: budget
    let remaining = rec.budget - rec.spent;
    if remaining <= 0.0 {
        tracing::info!(agent_id, "no budget remaining");
        return Ok(None);
    }

    // Guard: checkpoint must exist
    let checkpoint_data = find_checkpoint(&conn, agent_id)?;
    let checkpoint_data = match checkpoint_data {
        Some(c) => c,
        None => {
            tracing::info!(agent_id, "no checkpoint found");
            return Ok(None);
        }
    };

    // All guards passed — spawn continuation
    let new_version = rec.respawn_count + 1;
    let continuation_name = format!("{}-v{new_version}", rec.agent_name);
    let new_id = uuid::Uuid::new_v4().to_string();

    insert_continuation(
        &conn,
        &new_id,
        &continuation_name,
        &rec,
        new_version,
        agent_id,
        remaining,
    )?;
    drop(conn);

    spawn_continuation(
        pool,
        &new_id,
        &continuation_name,
        &rec,
        new_version,
        &checkpoint_data,
        daemon_url,
        repo_root,
    )?;

    tracing::info!(
        old_agent = agent_id,
        new_agent = new_id.as_str(),
        version = new_version,
        "auto-respawned continuation agent"
    );
    Ok(Some(new_id))
}

fn load_agent(conn: &rusqlite::Connection, agent_id: &str) -> RuntimeResult<AgentRecord> {
    conn.query_row(
        "SELECT agent_name, org_id, task_id, model, budget_usd, spent_usd, \
         respawn_count, max_respawns FROM art_agents WHERE id = ?1",
        [agent_id],
        |r| {
            Ok(AgentRecord {
                agent_name: r.get(0)?,
                org_id: r.get(1)?,
                task_id: r.get(2)?,
                model: r.get(3)?,
                budget: r.get(4)?,
                spent: r.get(5)?,
                respawn_count: r.get(6)?,
                max_respawns: r.get(7)?,
            })
        },
    )
    .map_err(|e| RuntimeError::Internal(format!("agent not found: {e}")))
}

fn find_checkpoint(conn: &rusqlite::Connection, agent_id: &str) -> RuntimeResult<Option<String>> {
    // Check art_context first
    let cp: Option<String> = conn
        .query_row(
            "SELECT value FROM art_context WHERE agent_id = ?1 AND key = 'checkpoint_state'",
            [agent_id],
            |r| r.get(0),
        )
        .ok();
    if cp.is_some() {
        return Ok(cp);
    }
    // Fallback: lr_checkpoints (may not exist if longrunning ext not loaded)
    let lr: Option<String> = conn
        .query_row(
            "SELECT state FROM lr_checkpoints WHERE execution_id = ?1 \
             ORDER BY id DESC LIMIT 1",
            [agent_id],
            |r| r.get(0),
        )
        .ok();
    Ok(lr)
}

fn insert_continuation(
    conn: &rusqlite::Connection,
    new_id: &str,
    name: &str,
    rec: &AgentRecord,
    version: i32,
    parent_id: &str,
    remaining_budget: f64,
) -> RuntimeResult<()> {
    conn.execute(
        "INSERT INTO art_agents (id, agent_name, org_id, task_id, stage, model, \
         node, budget_usd, respawn_count, parent_agent_id, max_respawns, \
         created_at, updated_at) \
         VALUES (?1,?2,?3,?4,'spawning',?5,'local',?6,?7,?8,?9, \
         datetime('now'),datetime('now'))",
        params![
            new_id,
            name,
            rec.org_id,
            rec.task_id,
            rec.model,
            remaining_budget,
            version,
            parent_id,
            rec.max_respawns,
        ],
    )
    .map_err(|e| RuntimeError::Internal(format!("insert continuation: {e}")))?;
    Ok(())
}

fn build_instructions(name: &str, version: i32, max: i32, checkpoint: &str) -> String {
    format!(
        "Sei la continuazione dell'agente {name} (v{version}/{max}).\n\
         L'agente precedente ha salvato un checkpoint prima di esaurire il contesto.\n\n\
         ## Checkpoint\n{checkpoint}\n\n\
         ## Istruzioni\n\
         1. Leggi il checkpoint sopra per capire cosa e' stato fatto\n\
         2. Riprendi il lavoro da dove si e' fermato l'agente precedente\n\
         3. Se il tuo contesto si riempie, salva un checkpoint\n\
         4. PUT /api/agents/<tuo-id>/context/checkpoint_state con il tuo stato"
    )
}

#[allow(clippy::too_many_arguments)]
fn spawn_continuation(
    pool: &ConnPool,
    new_id: &str,
    name: &str,
    rec: &AgentRecord,
    version: i32,
    checkpoint: &str,
    daemon_url: &str,
    repo_root: &str,
) -> RuntimeResult<()> {
    let instructions = build_instructions(name, version, rec.max_respawns, checkpoint);
    let workspace = crate::spawner::create_worktree(std::path::Path::new(repo_root), name)?;
    crate::spawner::write_instructions(&workspace, &instructions)?;

    let backend = crate::spawner::backend_for_tier("t2", rec.model.as_deref());
    let task_id_str = rec.task_id.map(|t| t.to_string());
    let mut env: Vec<(&str, &str)> = vec![
        ("CONVERGIO_AGENT_NAME", name),
        ("CONVERGIO_ORG", &rec.org_id),
        ("CONVERGIO_DAEMON_URL", daemon_url),
        ("CONVERGIO_AGENT_ID", new_id),
    ];
    if let Some(ref tid) = task_id_str {
        env.push(("CONVERGIO_TASK_ID", tid.as_str()));
    }

    let spawned = crate::spawner::spawn_process(&workspace, &backend, &env, 3600, None)?;

    // Activate in DB
    let conn = pool.get()?;
    conn.execute(
        "UPDATE art_agents SET stage = 'running', workspace_path = ?1, \
         updated_at = datetime('now') WHERE id = ?2",
        params![workspace.to_string_lossy().to_string(), new_id],
    )
    .map_err(|e| RuntimeError::Internal(format!("activate continuation: {e}")))?;

    // Seed context + copy checkpoint
    let _ = crate::context::seed(&conn, new_id, rec.task_id, &rec.org_id);
    let _ = crate::context::set(&conn, new_id, "checkpoint_state", checkpoint, "system");
    drop(conn);

    crate::spawn_monitor::monitor_agent(
        pool.clone(),
        new_id.to_string(),
        spawned.pid,
        workspace.to_string_lossy().to_string(),
        repo_root.to_string(),
    );
    Ok(())
}

#[cfg(test)]
#[path = "respawn_tests.rs"]
mod tests;
