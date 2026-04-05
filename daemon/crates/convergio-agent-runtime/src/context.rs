//! Per-agent live context: CRUD operations on art_context.

use rusqlite::params;
use serde::{Deserialize, Serialize};

use crate::types::{RuntimeError, RuntimeResult};

/// A single context key-value entry for an agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextEntry {
    pub agent_id: String,
    pub key: String,
    pub value: String,
    pub version: i64,
    pub set_by: String,
    pub updated_at: String,
}

/// List all context entries for an agent.
pub fn list(conn: &rusqlite::Connection, agent_id: &str) -> RuntimeResult<Vec<ContextEntry>> {
    let mut stmt = conn.prepare(
        "SELECT agent_id, key, value, version, set_by, updated_at \
         FROM art_context WHERE agent_id = ?1 ORDER BY key",
    )?;
    let rows = stmt.query_map(params![agent_id], |r| {
        Ok(ContextEntry {
            agent_id: r.get(0)?,
            key: r.get(1)?,
            value: r.get(2)?,
            version: r.get(3)?,
            set_by: r.get(4)?,
            updated_at: r.get(5)?,
        })
    })?;
    let mut out = Vec::new();
    for row in rows {
        out.push(row?);
    }
    Ok(out)
}

/// Get a single context entry.
pub fn get(
    conn: &rusqlite::Connection,
    agent_id: &str,
    key: &str,
) -> RuntimeResult<Option<ContextEntry>> {
    let mut stmt = conn.prepare(
        "SELECT agent_id, key, value, version, set_by, updated_at \
         FROM art_context WHERE agent_id = ?1 AND key = ?2",
    )?;
    let mut rows = stmt.query_map(params![agent_id, key], |r| {
        Ok(ContextEntry {
            agent_id: r.get(0)?,
            key: r.get(1)?,
            value: r.get(2)?,
            version: r.get(3)?,
            set_by: r.get(4)?,
            updated_at: r.get(5)?,
        })
    })?;
    match rows.next() {
        Some(row) => Ok(Some(row?)),
        None => Ok(None),
    }
}

/// Set a context entry (upsert with version increment).
pub fn set(
    conn: &rusqlite::Connection,
    agent_id: &str,
    key: &str,
    value: &str,
    set_by: &str,
) -> RuntimeResult<ContextEntry> {
    conn.execute(
        "INSERT INTO art_context (agent_id, key, value, version, set_by) \
         VALUES (?1, ?2, ?3, 1, ?4) \
         ON CONFLICT(agent_id, key) DO UPDATE SET \
           value = excluded.value, \
           version = art_context.version + 1, \
           set_by = excluded.set_by, \
           updated_at = datetime('now')",
        params![agent_id, key, value, set_by],
    )?;
    get(conn, agent_id, key)?
        .ok_or_else(|| RuntimeError::Internal("upsert succeeded but row missing".into()))
}

/// Delete a context entry. Returns true if a row was deleted.
pub fn delete(conn: &rusqlite::Connection, agent_id: &str, key: &str) -> RuntimeResult<bool> {
    let n = conn.execute(
        "DELETE FROM art_context WHERE agent_id = ?1 AND key = ?2",
        params![agent_id, key],
    )?;
    Ok(n > 0)
}

/// Seed initial context for a newly spawned agent.
///
/// Inserts org_id, and if task_id is present, also task_id,
/// instructions, and plan_id from the tasks table.
/// Uses INSERT OR IGNORE so repeated calls are safe.
pub fn seed(
    conn: &rusqlite::Connection,
    agent_id: &str,
    task_id: Option<i64>,
    org_id: &str,
) -> RuntimeResult<usize> {
    let mut count = 0usize;
    count += conn.execute(
        "INSERT OR IGNORE INTO art_context \
         (agent_id, key, value, set_by) VALUES (?1, 'org_id', ?2, 'system')",
        params![agent_id, org_id],
    )?;
    if let Some(tid) = task_id {
        count += conn.execute(
            "INSERT OR IGNORE INTO art_context \
             (agent_id, key, value, set_by) VALUES (?1, 'task_id', ?2, 'system')",
            params![agent_id, tid.to_string()],
        )?;
        // Pull instructions and plan_id from tasks table if it exists
        let task_row: Option<(Option<String>, Option<i64>)> = conn
            .query_row(
                "SELECT instructions, plan_id FROM tasks WHERE id = ?1",
                params![tid],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .ok();
        if let Some((instr, plan_id)) = task_row {
            if let Some(i) = instr {
                count += conn.execute(
                    "INSERT OR IGNORE INTO art_context \
                     (agent_id, key, value, set_by) \
                     VALUES (?1, 'instructions', ?2, 'system')",
                    params![agent_id, i],
                )?;
            }
            if let Some(pid) = plan_id {
                count += conn.execute(
                    "INSERT OR IGNORE INTO art_context \
                     (agent_id, key, value, set_by) \
                     VALUES (?1, 'plan_id', ?2, 'system')",
                    params![agent_id, pid.to_string()],
                )?;
            }
        }
    }
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute(
            "INSERT INTO art_agents (id, agent_name, org_id, node) \
             VALUES ('a1', 'test-agent', 'org-1', 'localhost')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn test_set_and_get() {
        let conn = setup();
        let entry = set(&conn, "a1", "model", "opus-4", "agent").unwrap();
        assert_eq!(entry.key, "model");
        assert_eq!(entry.value, "opus-4");
        assert_eq!(entry.version, 1);
        let got = get(&conn, "a1", "model").unwrap().unwrap();
        assert_eq!(got.value, "opus-4");
    }

    #[test]
    fn test_list() {
        let conn = setup();
        set(&conn, "a1", "alpha", "1", "agent").unwrap();
        set(&conn, "a1", "beta", "2", "agent").unwrap();
        let entries = list(&conn, "a1").unwrap();
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].key, "alpha");
        assert_eq!(entries[1].key, "beta");
    }

    #[test]
    fn test_delete() {
        let conn = setup();
        set(&conn, "a1", "tmp", "x", "agent").unwrap();
        assert!(delete(&conn, "a1", "tmp").unwrap());
        assert!(!delete(&conn, "a1", "tmp").unwrap());
        assert!(get(&conn, "a1", "tmp").unwrap().is_none());
    }

    #[test]
    fn test_upsert_increments_version() {
        let conn = setup();
        let v1 = set(&conn, "a1", "k", "val1", "agent").unwrap();
        assert_eq!(v1.version, 1);
        let v2 = set(&conn, "a1", "k", "val2", "agent").unwrap();
        assert_eq!(v2.version, 2);
        assert_eq!(v2.value, "val2");
    }

    #[test]
    fn test_seed_basic() {
        let conn = setup();
        let count = seed(&conn, "a1", None, "org-1").unwrap();
        assert_eq!(count, 1);
        let entry = get(&conn, "a1", "org_id").unwrap().unwrap();
        assert_eq!(entry.value, "org-1");
    }
}
