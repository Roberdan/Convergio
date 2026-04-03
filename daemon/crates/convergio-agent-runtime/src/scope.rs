//! Scope enforcement — agents can only access resources assigned to their task.
//!
//! Every agent gets explicit scope rules when spawned. The runtime checks
//! access before allowing file/table operations.

use rusqlite::{params, Connection};

use crate::types::{RuntimeError, RuntimeResult};

/// Access level for a scope rule.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AccessLevel {
    Read,
    Write,
}

impl AccessLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Read => "read",
            Self::Write => "write",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "read" => Some(Self::Read),
            "write" => Some(Self::Write),
            _ => None,
        }
    }
}

/// Grant access to a resource for an agent.
pub fn grant(
    conn: &Connection,
    agent_id: &str,
    resource: &str,
    access: &AccessLevel,
) -> RuntimeResult<()> {
    conn.execute(
        "INSERT OR IGNORE INTO art_scope_rules (agent_id, resource, access) \
         VALUES (?1, ?2, ?3)",
        params![agent_id, resource, access.as_str()],
    )?;
    tracing::debug!(
        agent_id,
        resource,
        access = access.as_str(),
        "scope granted"
    );
    Ok(())
}

/// Revoke all scope rules for an agent (on stop/reap).
pub fn revoke_all(conn: &Connection, agent_id: &str) -> RuntimeResult<()> {
    conn.execute(
        "DELETE FROM art_scope_rules WHERE agent_id = ?1",
        params![agent_id],
    )?;
    Ok(())
}

/// Check if an agent has access to a resource at the given level.
/// Write access implies read access.
pub fn check(
    conn: &Connection,
    agent_id: &str,
    resource: &str,
    access: &AccessLevel,
) -> RuntimeResult<bool> {
    let count: i64 = if *access == AccessLevel::Read {
        // Read allowed if they have read OR write
        conn.query_row(
            "SELECT COUNT(*) FROM art_scope_rules \
             WHERE agent_id = ?1 AND resource = ?2",
            params![agent_id, resource],
            |r| r.get(0),
        )?
    } else {
        conn.query_row(
            "SELECT COUNT(*) FROM art_scope_rules \
             WHERE agent_id = ?1 AND resource = ?2 AND access = 'write'",
            params![agent_id, resource],
            |r| r.get(0),
        )?
    };
    Ok(count > 0)
}

/// Enforce scope: returns Ok if allowed, Err(ScopeViolation) if not.
pub fn enforce(
    conn: &Connection,
    agent_id: &str,
    resource: &str,
    access: &AccessLevel,
) -> RuntimeResult<()> {
    if check(conn, agent_id, resource, access)? {
        Ok(())
    } else {
        Err(RuntimeError::ScopeViolation {
            agent_id: agent_id.into(),
            resource: resource.into(),
        })
    }
}

/// List all scope rules for an agent.
pub fn list_rules(conn: &Connection, agent_id: &str) -> RuntimeResult<Vec<(String, String)>> {
    let mut stmt = conn.prepare(
        "SELECT resource, access FROM art_scope_rules \
         WHERE agent_id = ?1 ORDER BY resource",
    )?;
    let rows = stmt.query_map(params![agent_id], |row| {
        Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
    })?;
    let mut rules = Vec::new();
    for row in rows {
        rules.push(row?);
    }
    Ok(rules)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::schema;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        // Insert a dummy agent for FK
        conn.execute(
            "INSERT INTO art_agents (id, agent_name, org_id, node) \
             VALUES ('a1', 'elena', 'legal-corp', 'n1')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn grant_and_check_write() {
        let conn = setup();
        grant(&conn, "a1", "/workspace/contract.md", &AccessLevel::Write).unwrap();
        assert!(check(&conn, "a1", "/workspace/contract.md", &AccessLevel::Write).unwrap());
        // Write implies read
        assert!(check(&conn, "a1", "/workspace/contract.md", &AccessLevel::Read).unwrap());
    }

    #[test]
    fn read_only_blocks_write() {
        let conn = setup();
        grant(&conn, "a1", "/workspace/readme.md", &AccessLevel::Read).unwrap();
        assert!(check(&conn, "a1", "/workspace/readme.md", &AccessLevel::Read).unwrap());
        assert!(!check(&conn, "a1", "/workspace/readme.md", &AccessLevel::Write).unwrap());
    }

    #[test]
    fn enforce_returns_scope_violation() {
        let conn = setup();
        let err = enforce(&conn, "a1", "/secret/file.key", &AccessLevel::Read).unwrap_err();
        assert!(err.to_string().contains("scope violation"));
    }

    #[test]
    fn revoke_all_clears_rules() {
        let conn = setup();
        grant(&conn, "a1", "/a", &AccessLevel::Write).unwrap();
        grant(&conn, "a1", "/b", &AccessLevel::Read).unwrap();
        revoke_all(&conn, "a1").unwrap();
        let rules = list_rules(&conn, "a1").unwrap();
        assert!(rules.is_empty());
    }
}
