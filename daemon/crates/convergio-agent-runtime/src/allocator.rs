//! Agent allocator — spawn agents with budget, capability, org, model preference.
//!
//! The daemon decides where to run (node, model) based on available slots
//! and the agent's requirements.

use rusqlite::{params, Connection};
use uuid::Uuid;

use crate::types::{AgentInstance, AgentStage, RuntimeResult, SpawnRequest};

/// Spawn a new agent instance. Returns the allocated agent ID.
pub fn spawn(conn: &Connection, req: &SpawnRequest, node: &str) -> RuntimeResult<String> {
    let id = Uuid::new_v4().to_string();
    let workspace = format!("/tmp/cvg-agent-{}", &id[..8]);

    conn.execute(
        "INSERT INTO art_agents \
         (id, agent_name, org_id, task_id, stage, workspace_path, \
          model, node, budget_usd, priority) \
         VALUES (?1, ?2, ?3, ?4, 'spawning', ?5, ?6, ?7, ?8, ?9)",
        params![
            id,
            req.agent_name,
            req.org_id,
            req.task_id,
            workspace,
            req.model_preference,
            node,
            req.budget_usd,
            req.priority,
        ],
    )?;

    tracing::info!(
        agent_id = id.as_str(),
        agent_name = req.agent_name.as_str(),
        org = req.org_id.as_str(),
        node,
        "agent spawned"
    );
    Ok(id)
}

/// Transition an agent to running stage after workspace setup.
pub fn activate(conn: &Connection, agent_id: &str) -> RuntimeResult<()> {
    let updated = conn.execute(
        "UPDATE art_agents SET stage = 'running', updated_at = datetime('now') \
         WHERE id = ?1 AND stage = 'spawning'",
        params![agent_id],
    )?;
    if updated == 0 {
        return Err(crate::types::RuntimeError::NotFound(format!(
            "agent {agent_id} not in spawning stage"
        )));
    }
    Ok(())
}

/// Stop an agent (graceful shutdown).
pub fn stop(conn: &Connection, agent_id: &str) -> RuntimeResult<()> {
    conn.execute(
        "UPDATE art_agents SET stage = 'stopped', updated_at = datetime('now') \
         WHERE id = ?1 AND stage NOT IN ('stopped', 'reaped')",
        params![agent_id],
    )?;
    Ok(())
}

/// Stop all agents in an org (org death or budget exhaustion).
pub fn stop_org(conn: &Connection, org_id: &str) -> RuntimeResult<usize> {
    let n = conn.execute(
        "UPDATE art_agents SET stage = 'stopped', updated_at = datetime('now') \
         WHERE org_id = ?1 AND stage NOT IN ('stopped', 'reaped')",
        params![org_id],
    )?;
    if n > 0 {
        tracing::warn!(org_id, count = n, "stopped all agents in org");
    }
    Ok(n)
}

/// Get a single agent instance by ID.
pub fn get(conn: &Connection, agent_id: &str) -> RuntimeResult<AgentInstance> {
    conn.query_row(
        "SELECT id, agent_name, org_id, task_id, stage, workspace_path, \
         model, node, budget_usd, spent_usd, priority, created_at \
         FROM art_agents WHERE id = ?1",
        params![agent_id],
        map_agent,
    )
    .map_err(|e| match e {
        rusqlite::Error::QueryReturnedNoRows => {
            crate::types::RuntimeError::NotFound(agent_id.into())
        }
        other => other.into(),
    })
}

/// List active agents, optionally filtered by org.
pub fn list_active(conn: &Connection, org_id: Option<&str>) -> RuntimeResult<Vec<AgentInstance>> {
    let sql = if org_id.is_some() {
        "SELECT id, agent_name, org_id, task_id, stage, workspace_path, \
         model, node, budget_usd, spent_usd, priority, created_at \
         FROM art_agents WHERE stage IN ('spawning','running','borrowed') \
         AND org_id = ?1 ORDER BY priority DESC, created_at ASC"
    } else {
        "SELECT id, agent_name, org_id, task_id, stage, workspace_path, \
         model, node, budget_usd, spent_usd, priority, created_at \
         FROM art_agents WHERE stage IN ('spawning','running','borrowed') \
         ORDER BY priority DESC, created_at ASC"
    };
    let mut stmt = conn.prepare(sql)?;
    let rows = if let Some(oid) = org_id {
        stmt.query_map(params![oid], map_agent)?
    } else {
        stmt.query_map([], map_agent)?
    };
    let mut agents = Vec::new();
    for row in rows {
        agents.push(row?);
    }
    Ok(agents)
}

fn map_agent(row: &rusqlite::Row<'_>) -> rusqlite::Result<AgentInstance> {
    let stage_str: String = row.get(4)?;
    let stage = AgentStage::parse(&stage_str).unwrap_or(AgentStage::Stopped);
    Ok(AgentInstance {
        id: row.get(0)?,
        agent_name: row.get(1)?,
        org_id: row.get(2)?,
        task_id: row.get(3)?,
        stage,
        workspace_path: row.get(5)?,
        model: row.get(6)?,
        node: row.get(7)?,
        budget_usd: row.get(8)?,
        spent_usd: row.get(9)?,
        priority: row.get(10)?,
        created_at: row.get(11)?,
        last_heartbeat: None,
    })
}

#[cfg(test)]
#[path = "allocator_tests.rs"]
mod tests;
