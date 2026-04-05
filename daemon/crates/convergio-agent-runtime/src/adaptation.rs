//! Agent live adaptation — poll for updates and sentinel files.
//!
//! Agents call `poll_updates` periodically to discover plan/task status
//! changes, new context entries, pending IPC messages, and sentinel signals
//! (STOP, PRIORITY_CHANGE, CHECKPOINT_READY).

use rusqlite::params;
use serde::{Deserialize, Serialize};

use crate::types::{RuntimeError, RuntimeResult};

/// All updates available for an agent since a given timestamp.
#[derive(Debug, Serialize, Deserialize)]
pub struct AgentUpdates {
    pub agent_id: String,
    pub since: String,
    pub plan_status: Option<String>,
    pub task_status: Option<String>,
    pub context_changes: Vec<ContextChange>,
    pub pending_messages: i64,
    pub sentinel: Option<String>,
}

/// A context entry that changed since the last poll.
#[derive(Debug, Serialize, Deserialize)]
pub struct ContextChange {
    pub key: String,
    pub value: String,
    pub version: i64,
    pub updated_at: String,
}

/// Fetch all updates for an agent since a given timestamp.
pub fn poll_updates(
    conn: &rusqlite::Connection,
    agent_id: &str,
    since: &str,
) -> RuntimeResult<AgentUpdates> {
    // 1. Get agent record
    let row: (Option<i64>, Option<String>, String) = conn
        .query_row(
            "SELECT task_id, workspace_path, agent_name FROM art_agents WHERE id = ?1",
            params![agent_id],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )
        .map_err(|e| match e {
            rusqlite::Error::QueryReturnedNoRows => RuntimeError::NotFound(agent_id.to_string()),
            other => RuntimeError::Db(other),
        })?;
    let (task_id, workspace_path, agent_name) = row;

    // 2. Plan + task status
    let (plan_status, task_status) = query_plan_task(conn, task_id);

    // 3. Context changes since timestamp
    let context_changes = query_context_changes(conn, agent_id, since)?;

    // 4. Pending IPC messages
    let pending_messages: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM ipc_messages WHERE to_agent = ?1 AND read_at IS NULL",
            params![agent_name],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // 5. Sentinel check
    let sentinel = workspace_path.as_deref().and_then(check_sentinel);

    Ok(AgentUpdates {
        agent_id: agent_id.to_string(),
        since: since.to_string(),
        plan_status,
        task_status,
        context_changes,
        pending_messages,
        sentinel,
    })
}

fn query_plan_task(
    conn: &rusqlite::Connection,
    task_id: Option<i64>,
) -> (Option<String>, Option<String>) {
    let Some(tid) = task_id else {
        return (None, None);
    };
    let row: Option<(String, Option<i64>)> = conn
        .query_row(
            "SELECT status, plan_id FROM tasks WHERE id = ?1",
            params![tid],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .ok();
    let Some((task_status, plan_id)) = row else {
        return (None, None);
    };
    let plan_status = plan_id.and_then(|pid| {
        conn.query_row(
            "SELECT status FROM plans WHERE id = ?1",
            params![pid],
            |r| r.get::<_, String>(0),
        )
        .ok()
    });
    (plan_status, Some(task_status))
}

fn query_context_changes(
    conn: &rusqlite::Connection,
    agent_id: &str,
    since: &str,
) -> RuntimeResult<Vec<ContextChange>> {
    let mut stmt = conn.prepare(
        "SELECT key, value, version, updated_at FROM art_context \
         WHERE agent_id = ?1 AND updated_at > ?2 ORDER BY updated_at",
    )?;
    let rows = stmt.query_map(params![agent_id, since], |r| {
        Ok(ContextChange {
            key: r.get(0)?,
            value: r.get(1)?,
            version: r.get(2)?,
            updated_at: r.get(3)?,
        })
    })?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

/// Check for sentinel files in an agent workspace.
pub fn check_sentinel(workspace: &str) -> Option<String> {
    let sentinel_dir = std::path::Path::new(workspace).join(".convergio");
    for name in ["STOP", "PRIORITY_CHANGE", "CHECKPOINT_READY"] {
        if sentinel_dir.join(name).exists() {
            return Some(name.to_string());
        }
    }
    None
}

/// Write a sentinel file to an agent's workspace.
pub fn write_sentinel(workspace: &str, sentinel: &str) -> RuntimeResult<()> {
    let dir = std::path::Path::new(workspace).join(".convergio");
    std::fs::create_dir_all(&dir).map_err(|e| RuntimeError::Internal(format!("mkdir: {e}")))?;
    std::fs::write(dir.join(sentinel), "")
        .map_err(|e| RuntimeError::Internal(format!("write sentinel: {e}")))?;
    Ok(())
}

/// Clear a sentinel file after it has been processed.
pub fn clear_sentinel(workspace: &str, sentinel: &str) -> RuntimeResult<()> {
    let path = std::path::Path::new(workspace)
        .join(".convergio")
        .join(sentinel);
    if path.exists() {
        std::fs::remove_file(&path)
            .map_err(|e| RuntimeError::Internal(format!("rm sentinel: {e}")))?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_sentinel_none() {
        // Non-existent directory returns None
        assert!(check_sentinel("/tmp/no-such-dir-convergio").is_none());
    }

    #[test]
    fn test_write_and_check_sentinel() {
        let dir = tempfile::tempdir().unwrap();
        let ws = dir.path().to_str().unwrap();
        write_sentinel(ws, "STOP").unwrap();
        assert_eq!(check_sentinel(ws), Some("STOP".to_string()));
    }

    #[test]
    fn test_clear_sentinel() {
        let dir = tempfile::tempdir().unwrap();
        let ws = dir.path().to_str().unwrap();
        write_sentinel(ws, "STOP").unwrap();
        clear_sentinel(ws, "STOP").unwrap();
        assert!(check_sentinel(ws).is_none());
    }

    #[test]
    fn test_poll_updates_no_agent() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let err = poll_updates(&conn, "nonexistent", "1970-01-01").unwrap_err();
        assert!(err.to_string().contains("not found"));
    }
}
