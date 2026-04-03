//! Delegation chain — tree of parent-child execution relationships.
//!
//! Tracks the complete delegation tree with budget/deadline propagation
//! and death cascade (parent reaped => children reaped).

use rusqlite::{params, Connection};

use crate::types::{DelegationNode, ExecutionStage, LongRunResult};

/// Register a child execution under a parent.
pub fn create_child(
    conn: &Connection,
    child_id: &str,
    parent_id: &str,
    agent: &str,
    node: &str,
    budget_usd: f64,
    deadline: Option<&str>,
) -> LongRunResult<()> {
    conn.execute(
        "INSERT INTO lr_executions \
         (id, agent, node, parent_id, budget_usd, deadline, stage) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'starting')",
        params![child_id, agent, node, parent_id, budget_usd, deadline],
    )?;
    tracing::info!(child_id, parent_id, agent, "delegation child created");
    Ok(())
}

/// Build the full delegation tree rooted at `root_id`.
pub fn build_tree(conn: &Connection, root_id: &str) -> LongRunResult<Option<DelegationNode>> {
    let root = load_node(conn, root_id)?;
    match root {
        Some(mut node) => {
            populate_children(conn, &mut node)?;
            Ok(Some(node))
        }
        None => Ok(None),
    }
}

/// List direct children of an execution.
pub fn list_children(conn: &Connection, parent_id: &str) -> LongRunResult<Vec<DelegationNode>> {
    let mut stmt = conn.prepare(
        "SELECT id, parent_id, agent, node, budget_usd, deadline, stage \
         FROM lr_executions WHERE parent_id = ?1 ORDER BY created_at",
    )?;
    let rows = stmt.query_map(params![parent_id], map_row)?;
    let mut children = Vec::new();
    for row in rows {
        children.push(row?);
    }
    Ok(children)
}

/// Cascade death: mark all descendants of a reaped execution as reaped.
pub fn cascade_death(conn: &Connection, parent_id: &str) -> LongRunResult<usize> {
    // Recursive CTE to find all descendants
    let n = conn.execute(
        "WITH RECURSIVE descendants(id) AS ( \
             SELECT id FROM lr_executions WHERE parent_id = ?1 \
             UNION ALL \
             SELECT e.id FROM lr_executions e \
             JOIN descendants d ON e.parent_id = d.id \
         ) \
         UPDATE lr_executions SET stage = 'reaped', \
         updated_at = datetime('now') \
         WHERE id IN (SELECT id FROM descendants) \
         AND stage NOT IN ('completing', 'failed', 'reaped')",
        params![parent_id],
    )?;
    if n > 0 {
        tracing::warn!(parent_id, descendants_reaped = n, "death cascaded");
    }
    Ok(n)
}

fn load_node(conn: &Connection, id: &str) -> LongRunResult<Option<DelegationNode>> {
    let result = conn.query_row(
        "SELECT id, parent_id, agent, node, budget_usd, deadline, stage \
         FROM lr_executions WHERE id = ?1",
        params![id],
        map_row,
    );
    match result {
        Ok(node) => Ok(Some(node)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

fn populate_children(conn: &Connection, node: &mut DelegationNode) -> LongRunResult<()> {
    let children = list_children(conn, &node.execution_id)?;
    for mut child in children {
        populate_children(conn, &mut child)?;
        node.children.push(child);
    }
    Ok(())
}

fn map_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<DelegationNode> {
    let stage_str: String = row.get(6)?;
    let stage = ExecutionStage::parse(&stage_str).unwrap_or(ExecutionStage::Running);
    Ok(DelegationNode {
        execution_id: row.get(0)?,
        parent_id: row.get(1)?,
        agent: row.get(2)?,
        node: row.get(3)?,
        budget_usd: row.get(4)?,
        deadline: row.get(5)?,
        stage,
        children: Vec::new(),
    })
}

#[cfg(test)]
#[path = "delegation_tests.rs"]
mod tests;
