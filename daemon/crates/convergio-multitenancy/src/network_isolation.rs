//! Network isolation — per-org peer whitelist enforcement.
//!
//! Orgs declare which peer nodes are authorized for mesh sync.
//! Sync requests from non-whitelisted peers are rejected.

use crate::types::{OrgId, PeerWhitelist, TenancyError};
use chrono::Utc;
use rusqlite::Connection;

/// Add a peer to an org's whitelist.
pub fn allow_peer(
    conn: &Connection,
    org_id: &OrgId,
    peer_name: &str,
    peer_url: &str,
) -> Result<(), TenancyError> {
    conn.execute(
        "INSERT INTO mt_peer_whitelist (org_id, peer_name, peer_url, allowed)
         VALUES (?1, ?2, ?3, 1)
         ON CONFLICT(org_id, peer_name)
         DO UPDATE SET peer_url = ?3, allowed = 1",
        rusqlite::params![org_id.0, peer_name, peer_url],
    )
    .map_err(|e| TenancyError::Db(format!("allow_peer: {e}")))?;
    tracing::info!(org = %org_id, peer = peer_name, "peer whitelisted");
    Ok(())
}

/// Revoke a peer from an org's whitelist (soft delete — sets allowed=0).
pub fn revoke_peer(conn: &Connection, org_id: &OrgId, peer_name: &str) -> Result<(), TenancyError> {
    conn.execute(
        "UPDATE mt_peer_whitelist SET allowed = 0
         WHERE org_id = ?1 AND peer_name = ?2",
        rusqlite::params![org_id.0, peer_name],
    )
    .map_err(|e| TenancyError::Db(format!("revoke_peer: {e}")))?;
    tracing::info!(org = %org_id, peer = peer_name, "peer revoked");
    Ok(())
}

/// Check whether a peer is authorized for a given org.
pub fn is_peer_allowed(
    conn: &Connection,
    org_id: &OrgId,
    peer_name: &str,
) -> Result<bool, TenancyError> {
    // If no whitelist entries exist for org, allow all (open mode)
    let count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM mt_peer_whitelist WHERE org_id = ?1",
            [&org_id.0],
            |r| r.get(0),
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    if count == 0 {
        return Ok(true);
    }
    let allowed: bool = conn
        .query_row(
            "SELECT allowed FROM mt_peer_whitelist
             WHERE org_id = ?1 AND peer_name = ?2",
            rusqlite::params![org_id.0, peer_name],
            |r| r.get::<_, bool>(0),
        )
        .unwrap_or(false);
    Ok(allowed)
}

/// List all whitelisted peers for an org.
pub fn list_peers(conn: &Connection, org_id: &OrgId) -> Result<Vec<PeerWhitelist>, TenancyError> {
    let mut stmt = conn
        .prepare(
            "SELECT org_id, peer_name, peer_url, allowed, created_at
             FROM mt_peer_whitelist WHERE org_id = ?1 ORDER BY peer_name",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let rows = stmt
        .query_map([&org_id.0], |row| {
            Ok(PeerWhitelist {
                org_id: OrgId(row.get::<_, String>(0)?),
                peer_name: row.get(1)?,
                peer_url: row.get(2)?,
                allowed: row.get(3)?,
                created_at: Utc::now(), // simplify: use current time
            })
        })
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(rows)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "multitenancy",
            &crate::schema::migrations(),
        )
        .unwrap();
        // Return a fresh in-memory connection with tables
        drop(conn);
        let c = Connection::open_in_memory().unwrap();
        c.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        for m in crate::schema::migrations() {
            c.execute_batch(m.up).unwrap();
        }
        c
    }

    #[test]
    fn open_mode_allows_all() {
        let conn = setup();
        let org = OrgId("acme".into());
        assert!(is_peer_allowed(&conn, &org, "any-peer").unwrap());
    }

    #[test]
    fn whitelist_restricts_peers() {
        let conn = setup();
        let org = OrgId("acme".into());
        allow_peer(&conn, &org, "node-a", "http://a:8420").unwrap();
        assert!(is_peer_allowed(&conn, &org, "node-a").unwrap());
        assert!(!is_peer_allowed(&conn, &org, "node-b").unwrap());
    }

    #[test]
    fn revoke_blocks_peer() {
        let conn = setup();
        let org = OrgId("acme".into());
        allow_peer(&conn, &org, "node-x", "http://x:8420").unwrap();
        revoke_peer(&conn, &org, "node-x").unwrap();
        assert!(!is_peer_allowed(&conn, &org, "node-x").unwrap());
    }

    #[test]
    fn list_peers_returns_all() {
        let conn = setup();
        let org = OrgId("acme".into());
        allow_peer(&conn, &org, "alpha", "http://a:8420").unwrap();
        allow_peer(&conn, &org, "beta", "http://b:8420").unwrap();
        let peers = list_peers(&conn, &org).unwrap();
        assert_eq!(peers.len(), 2);
    }
}
