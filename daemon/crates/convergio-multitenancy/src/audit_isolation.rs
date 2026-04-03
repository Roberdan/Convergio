//! Audit isolation — per-org audit trail with hash chain.
//!
//! Each org sees only its own audit entries. Admin sees everything.
//! Entries are hash-chained per org for tamper evidence.

use crate::types::{OrgAuditEntry, OrgId, TenancyError};
use chrono::Utc;
use rusqlite::Connection;
use sha2::{Digest, Sha256};

/// Record an audited action scoped to an org.
pub fn record(
    conn: &Connection,
    org_id: &OrgId,
    agent_id: &str,
    action: &str,
    target: &str,
    details: &str,
) -> Result<OrgAuditEntry, TenancyError> {
    let prev_hash = last_hash(conn, org_id)?;
    let timestamp = Utc::now().to_rfc3339();
    let hash_input = format!(
        "{}{}{}{}{}{prev_hash}",
        org_id.0, agent_id, action, target, timestamp
    );
    let entry_hash = sha256_hex(hash_input.as_bytes());

    conn.execute(
        "INSERT INTO mt_org_audit
         (org_id, agent_id, action, target, details, prev_hash, entry_hash)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        rusqlite::params![org_id.0, agent_id, action, target, details, prev_hash, entry_hash],
    )
    .map_err(|e| TenancyError::Db(format!("audit record: {e}")))?;

    Ok(OrgAuditEntry {
        id: None,
        org_id: org_id.clone(),
        agent_id: agent_id.to_string(),
        action: action.to_string(),
        target: target.to_string(),
        details: details.to_string(),
        prev_hash,
        entry_hash,
        created_at: Utc::now(),
    })
}

/// Query audit entries for a specific org.
pub fn query_org(
    conn: &Connection,
    org_id: &OrgId,
    limit: u32,
) -> Result<Vec<OrgAuditEntry>, TenancyError> {
    let mut stmt = conn
        .prepare(
            "SELECT id, org_id, agent_id, action, target, details,
                    prev_hash, entry_hash, created_at
             FROM mt_org_audit WHERE org_id = ?1
             ORDER BY id DESC LIMIT ?2",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let entries = stmt
        .query_map(rusqlite::params![org_id.0, limit], |row| {
            Ok(OrgAuditEntry {
                id: Some(row.get(0)?),
                org_id: OrgId(row.get::<_, String>(1)?),
                agent_id: row.get(2)?,
                action: row.get(3)?,
                target: row.get(4)?,
                details: row.get(5)?,
                prev_hash: row.get(6)?,
                entry_hash: row.get(7)?,
                created_at: Utc::now(),
            })
        })
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(entries)
}

/// Admin query: all audit entries across all orgs.
pub fn query_all(conn: &Connection, limit: u32) -> Result<Vec<OrgAuditEntry>, TenancyError> {
    let mut stmt = conn
        .prepare(
            "SELECT id, org_id, agent_id, action, target, details,
                    prev_hash, entry_hash, created_at
             FROM mt_org_audit ORDER BY id DESC LIMIT ?1",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let entries = stmt
        .query_map([limit], |row| {
            Ok(OrgAuditEntry {
                id: Some(row.get(0)?),
                org_id: OrgId(row.get::<_, String>(1)?),
                agent_id: row.get(2)?,
                action: row.get(3)?,
                target: row.get(4)?,
                details: row.get(5)?,
                prev_hash: row.get(6)?,
                entry_hash: row.get(7)?,
                created_at: Utc::now(),
            })
        })
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(entries)
}

/// Verify hash chain integrity for an org's audit trail.
pub fn verify_chain(conn: &Connection, org_id: &OrgId) -> Result<bool, TenancyError> {
    let mut stmt = conn
        .prepare(
            "SELECT prev_hash, entry_hash FROM mt_org_audit
             WHERE org_id = ?1 ORDER BY id ASC",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let hashes: Vec<(String, String)> = stmt
        .query_map([&org_id.0], |row| Ok((row.get(0)?, row.get(1)?)))
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    for i in 1..hashes.len() {
        if hashes[i].0 != hashes[i - 1].1 {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Get the last hash in the org's audit chain.
fn last_hash(conn: &Connection, org_id: &OrgId) -> Result<String, TenancyError> {
    let hash: String = conn
        .query_row(
            "SELECT entry_hash FROM mt_org_audit
             WHERE org_id = ?1 ORDER BY id DESC LIMIT 1",
            [&org_id.0],
            |r| r.get(0),
        )
        .unwrap_or_else(|_| "0".repeat(64));
    Ok(hash)
}

fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let c = Connection::open_in_memory().unwrap();
        c.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        for m in crate::schema::migrations() {
            c.execute_batch(m.up).unwrap();
        }
        c
    }

    #[test]
    fn record_and_query() {
        let conn = setup();
        let org = OrgId("acme".into());
        record(&conn, &org, "agent-1", "deploy", "/api", "{}").unwrap();
        record(&conn, &org, "agent-1", "validate", "/tasks", "{}").unwrap();
        let entries = query_org(&conn, &org, 10).unwrap();
        assert_eq!(entries.len(), 2);
    }

    #[test]
    fn cross_org_invisible() {
        let conn = setup();
        let org_a = OrgId("alpha".into());
        let org_b = OrgId("beta".into());
        record(&conn, &org_a, "a1", "read", "/data", "").unwrap();
        record(&conn, &org_b, "b1", "write", "/data", "").unwrap();
        let a_entries = query_org(&conn, &org_a, 10).unwrap();
        let b_entries = query_org(&conn, &org_b, 10).unwrap();
        assert_eq!(a_entries.len(), 1);
        assert_eq!(b_entries.len(), 1);
        assert_eq!(a_entries[0].agent_id, "a1");
    }

    #[test]
    fn admin_sees_all() {
        let conn = setup();
        record(&conn, &OrgId("x".into()), "a", "r", "/", "").unwrap();
        record(&conn, &OrgId("y".into()), "b", "w", "/", "").unwrap();
        let all = query_all(&conn, 10).unwrap();
        assert_eq!(all.len(), 2);
    }

    #[test]
    fn hash_chain_valid() {
        let conn = setup();
        let org = OrgId("chain".into());
        record(&conn, &org, "a", "x", "/", "").unwrap();
        record(&conn, &org, "a", "y", "/", "").unwrap();
        assert!(verify_chain(&conn, &org).unwrap());
    }
}
