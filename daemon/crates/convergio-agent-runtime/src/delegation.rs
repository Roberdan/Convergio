//! Delegation — borrowing agents across tasks/orgs with timeout and auto-return.
//!
//! The owner org retains control. When delegation expires or completes,
//! the agent returns to its original stage.

use rusqlite::{params, Connection};
use uuid::Uuid;

use crate::types::{AgentStage, Delegation, RuntimeError, RuntimeResult};

/// Borrow an agent to another task/org.
/// Returns the delegation ID. The agent transitions to `borrowed` stage.
pub fn borrow_agent(
    conn: &Connection,
    agent_id: &str,
    to_org: &str,
    to_task_id: Option<i64>,
    budget_usd: f64,
    timeout_secs: u64,
) -> RuntimeResult<String> {
    // Verify agent exists and is running
    let (from_org, stage): (String, String) = conn
        .query_row(
            "SELECT org_id, stage FROM art_agents WHERE id = ?1",
            params![agent_id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .map_err(|_| RuntimeError::NotFound(agent_id.into()))?;

    if AgentStage::parse(&stage) != Some(AgentStage::Running) {
        return Err(RuntimeError::Internal(format!(
            "agent {agent_id} is {stage}, not running"
        )));
    }

    // Check for circular delegation
    if detect_circular(conn, agent_id, to_org)? {
        return Err(RuntimeError::DeadlockDetected {
            chain: format!("{from_org} -> {to_org} -> {from_org}"),
        });
    }

    let deleg_id = Uuid::new_v4().to_string();
    conn.execute(
        "INSERT INTO art_delegations \
         (id, agent_id, from_org, to_org, to_task_id, budget_usd, \
          timeout_s, expires_at) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, \
                 datetime('now', '+' || ?7 || ' seconds'))",
        params![
            deleg_id,
            agent_id,
            from_org,
            to_org,
            to_task_id,
            budget_usd,
            timeout_secs as i64,
        ],
    )?;

    // Transition agent to borrowed
    conn.execute(
        "UPDATE art_agents SET stage = 'borrowed', updated_at = datetime('now') \
         WHERE id = ?1",
        params![agent_id],
    )?;

    tracing::info!(
        delegation_id = deleg_id.as_str(),
        agent_id,
        from_org = from_org.as_str(),
        to_org,
        timeout_secs,
        "agent borrowed"
    );
    Ok(deleg_id)
}

/// Return a borrowed agent to its owner.
pub fn return_agent(conn: &Connection, delegation_id: &str) -> RuntimeResult<()> {
    let agent_id: String = conn
        .query_row(
            "SELECT agent_id FROM art_delegations \
             WHERE id = ?1 AND returned = 0",
            params![delegation_id],
            |r| r.get(0),
        )
        .map_err(|_| RuntimeError::NotFound(delegation_id.into()))?;

    conn.execute(
        "UPDATE art_delegations SET returned = 1 WHERE id = ?1",
        params![delegation_id],
    )?;
    conn.execute(
        "UPDATE art_agents SET stage = 'running', updated_at = datetime('now') \
         WHERE id = ?1",
        params![agent_id],
    )?;
    tracing::info!(
        delegation_id,
        agent_id = agent_id.as_str(),
        "agent returned"
    );
    Ok(())
}

/// Find expired delegations that need auto-return.
pub fn find_expired(conn: &Connection) -> RuntimeResult<Vec<Delegation>> {
    let mut stmt = conn.prepare(
        "SELECT id, agent_id, from_org, to_org, to_task_id, budget_usd, \
         timeout_s, created_at, expires_at, returned \
         FROM art_delegations \
         WHERE returned = 0 AND datetime('now') > expires_at",
    )?;
    let rows = stmt.query_map([], map_delegation)?;
    let mut expired = Vec::new();
    for row in rows {
        expired.push(row?);
    }
    Ok(expired)
}

/// Detect circular delegation: would delegating from agent's org to to_org
/// create a cycle? Checks if to_org already has an active delegation back
/// to the agent's owner org.
fn detect_circular(conn: &Connection, agent_id: &str, to_org: &str) -> RuntimeResult<bool> {
    let from_org: String = conn.query_row(
        "SELECT org_id FROM art_agents WHERE id = ?1",
        params![agent_id],
        |r| r.get(0),
    )?;
    // Check if to_org has delegated any agent TO from_org (would create cycle)
    let count: i64 = conn.query_row(
        "SELECT COUNT(*) FROM art_delegations \
         WHERE from_org = ?1 AND to_org = ?2 AND returned = 0",
        params![to_org, from_org],
        |r| r.get(0),
    )?;
    Ok(count > 0)
}

fn map_delegation(row: &rusqlite::Row<'_>) -> rusqlite::Result<Delegation> {
    Ok(Delegation {
        id: row.get(0)?,
        agent_id: row.get(1)?,
        from_org: row.get(2)?,
        to_org: row.get(3)?,
        to_task_id: row.get(4)?,
        budget_usd: row.get(5)?,
        timeout_secs: row.get::<_, i64>(6)? as u64,
        created_at: row.get(7)?,
        expires_at: row.get(8)?,
        returned: row.get::<_, i64>(9)? != 0,
    })
}

#[cfg(test)]
#[path = "delegation_tests.rs"]
mod tests;
