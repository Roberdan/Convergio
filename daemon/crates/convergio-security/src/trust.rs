//! Trust levels and secrets filtering for remote peer execution.

use rusqlite::Connection;
use serde::{Deserialize, Serialize};

/// Trust level assigned to a remote peer.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TrustLevel {
    Untrusted = 0,
    Basic = 1,
    Standard = 2,
    Elevated = 3,
    Owner = 4,
}

impl TrustLevel {
    pub fn from_i64(v: i64) -> Self {
        match v {
            1 => Self::Basic,
            2 => Self::Standard,
            3 => Self::Elevated,
            4 => Self::Owner,
            _ => Self::Untrusted,
        }
    }
}

/// Record of trust granted to a peer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeerTrustRecord {
    pub peer_name: String,
    pub trust_level: TrustLevel,
    pub granted_by: String,
    pub reason: String,
    pub granted_at: String,
    pub expires_at: Option<String>,
}

/// Rule controlling which env vars require which trust level.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecretFilter {
    pub env_var: String,
    pub min_trust_level: TrustLevel,
    pub description: String,
}

/// Set trust level for a peer.
pub fn set_trust(
    conn: &Connection,
    peer: &str,
    level: TrustLevel,
    granted_by: &str,
    reason: &str,
) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT INTO peer_trust (peer_name, trust_level, granted_by, reason)
         VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(peer_name) DO UPDATE SET
           trust_level = excluded.trust_level,
           granted_by  = excluded.granted_by,
           reason      = excluded.reason,
           granted_at  = datetime('now')",
        rusqlite::params![peer, level as i64, granted_by, reason],
    )?;
    Ok(())
}

/// Get trust level for a peer (default: Untrusted).
pub fn get_trust(conn: &Connection, peer: &str) -> TrustLevel {
    conn.query_row(
        "SELECT trust_level FROM peer_trust WHERE peer_name = ?1",
        [peer],
        |row| row.get::<_, i64>(0),
    )
    .map(TrustLevel::from_i64)
    .unwrap_or(TrustLevel::Untrusted)
}

/// List all trust records.
pub fn list_trust(conn: &Connection) -> Vec<PeerTrustRecord> {
    let mut stmt = match conn.prepare(
        "SELECT peer_name, trust_level, granted_by, reason, granted_at, expires_at
         FROM peer_trust ORDER BY peer_name",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map([], |row| {
        Ok(PeerTrustRecord {
            peer_name: row.get(0)?,
            trust_level: TrustLevel::from_i64(row.get(1)?),
            granted_by: row.get(2)?,
            reason: row.get(3)?,
            granted_at: row.get(4)?,
            expires_at: row.get(5)?,
        })
    })
    .map(|rows| rows.filter_map(|r| r.ok()).collect())
    .unwrap_or_default()
}

/// Check if a peer can access a specific secret.
pub fn can_access_secret(conn: &Connection, peer: &str, env_var: &str) -> bool {
    let peer_level = get_trust(conn, peer);
    let min_level: TrustLevel = conn
        .query_row(
            "SELECT min_trust_level FROM secret_filters WHERE env_var = ?1",
            [env_var],
            |row| row.get::<_, i64>(0),
        )
        .map(TrustLevel::from_i64)
        .unwrap_or(TrustLevel::Standard);
    peer_level >= min_level
}

/// Filter env vars for a peer based on trust level.
pub fn filter_env_for_peer(
    conn: &Connection,
    peer: &str,
    env: &[(String, String)],
) -> Vec<(String, String)> {
    env.iter()
        .filter(|(k, _)| can_access_secret(conn, peer, k))
        .cloned()
        .collect()
}

/// Register a secret filter rule.
pub fn register_secret_filter(
    conn: &Connection,
    env_var: &str,
    min_level: TrustLevel,
    description: &str,
) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT INTO secret_filters (env_var, min_trust_level, description)
         VALUES (?1, ?2, ?3)
         ON CONFLICT(env_var) DO UPDATE SET
           min_trust_level = excluded.min_trust_level,
           description     = excluded.description",
        rusqlite::params![env_var, min_level as i64, description],
    )?;
    Ok(())
}

/// List all secret filter rules.
pub fn list_secret_filters(conn: &Connection) -> Vec<SecretFilter> {
    let mut stmt = match conn.prepare(
        "SELECT env_var, min_trust_level, description FROM secret_filters ORDER BY env_var",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map([], |row| {
        Ok(SecretFilter {
            env_var: row.get(0)?,
            min_trust_level: TrustLevel::from_i64(row.get(1)?),
            description: row.get(2)?,
        })
    })
    .map(|rows| rows.filter_map(|r| r.ok()).collect())
    .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch(crate::schema::ALL_TABLES).unwrap();
        conn
    }

    #[test]
    fn test_set_and_get_trust() {
        let conn = setup_db();
        set_trust(
            &conn,
            "node-eu-1",
            TrustLevel::Standard,
            "admin",
            "verified org",
        )
        .unwrap();
        assert_eq!(get_trust(&conn, "node-eu-1"), TrustLevel::Standard);
    }

    #[test]
    fn test_default_untrusted() {
        let conn = setup_db();
        assert_eq!(get_trust(&conn, "unknown-peer"), TrustLevel::Untrusted);
    }

    #[test]
    fn test_filter_env_vars() {
        let conn = setup_db();
        set_trust(&conn, "peer-a", TrustLevel::Basic, "admin", "low trust").unwrap();
        register_secret_filter(&conn, "API_KEY", TrustLevel::Elevated, "production key").unwrap();
        register_secret_filter(&conn, "LOG_LEVEL", TrustLevel::Untrusted, "safe").unwrap();

        let env = vec![
            ("API_KEY".into(), "secret123".into()),
            ("LOG_LEVEL".into(), "debug".into()),
        ];
        let filtered = filter_env_for_peer(&conn, "peer-a", &env);
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].0, "LOG_LEVEL");
    }

    #[test]
    fn test_trust_levels_ordered() {
        assert!(TrustLevel::Untrusted < TrustLevel::Basic);
        assert!(TrustLevel::Basic < TrustLevel::Standard);
        assert!(TrustLevel::Standard < TrustLevel::Elevated);
        assert!(TrustLevel::Elevated < TrustLevel::Owner);
    }
}
