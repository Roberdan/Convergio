//! Sandbox policies for remote peer execution.

use rusqlite::Connection;
use serde::{Deserialize, Serialize};

use crate::trust::TrustLevel;

/// Resource limits and access rules for a sandboxed peer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxPolicy {
    pub peer_name: String,
    pub allow_network: bool,
    pub allow_disk_write: bool,
    pub max_cpu_seconds: u64,
    pub max_memory_mb: u64,
    pub allowed_commands: Vec<String>,
    pub blocked_paths: Vec<String>,
}

/// Default sandbox policy based on trust level.
pub fn sandbox_for_trust(peer_name: &str, trust: TrustLevel) -> SandboxPolicy {
    match trust {
        TrustLevel::Untrusted => SandboxPolicy {
            peer_name: peer_name.to_string(),
            allow_network: false,
            allow_disk_write: false,
            max_cpu_seconds: 60,
            max_memory_mb: 512,
            allowed_commands: vec![],
            blocked_paths: vec!["/etc".into(), "/var".into(), "/root".into()],
        },
        TrustLevel::Basic => SandboxPolicy {
            peer_name: peer_name.to_string(),
            allow_network: false,
            allow_disk_write: true,
            max_cpu_seconds: 300,
            max_memory_mb: 1024,
            allowed_commands: vec![
                "cargo".into(),
                "npm".into(),
                "git".into(),
                "ls".into(),
                "cat".into(),
            ],
            blocked_paths: vec!["/etc".into(), "/root".into()],
        },
        TrustLevel::Standard => SandboxPolicy {
            peer_name: peer_name.to_string(),
            allow_network: true,
            allow_disk_write: true,
            max_cpu_seconds: 3600,
            max_memory_mb: 4096,
            allowed_commands: vec![],
            blocked_paths: vec![],
        },
        TrustLevel::Elevated | TrustLevel::Owner => SandboxPolicy {
            peer_name: peer_name.to_string(),
            allow_network: true,
            allow_disk_write: true,
            max_cpu_seconds: 0,
            max_memory_mb: 0,
            allowed_commands: vec![],
            blocked_paths: vec![],
        },
    }
}

/// Get custom sandbox override for a peer (if any).
pub fn get_custom_sandbox(conn: &Connection, peer: &str) -> Option<SandboxPolicy> {
    conn.query_row(
        "SELECT peer_name, allow_network, allow_disk_write, max_cpu_seconds,
                max_memory_mb, allowed_commands, blocked_paths
         FROM sandbox_overrides WHERE peer_name = ?1",
        [peer],
        |row| {
            let cmds_json: String = row.get(5)?;
            let paths_json: String = row.get(6)?;
            Ok(SandboxPolicy {
                peer_name: row.get(0)?,
                allow_network: row.get::<_, i64>(1)? != 0,
                allow_disk_write: row.get::<_, i64>(2)? != 0,
                max_cpu_seconds: row.get::<_, i64>(3)? as u64,
                max_memory_mb: row.get::<_, i64>(4)? as u64,
                allowed_commands: serde_json::from_str(&cmds_json).unwrap_or_default(),
                blocked_paths: serde_json::from_str(&paths_json).unwrap_or_default(),
            })
        },
    )
    .ok()
}

/// Set custom sandbox override for a peer.
pub fn set_custom_sandbox(
    conn: &Connection,
    policy: &SandboxPolicy,
) -> Result<(), rusqlite::Error> {
    let cmds = serde_json::to_string(&policy.allowed_commands).unwrap_or_default();
    let paths = serde_json::to_string(&policy.blocked_paths).unwrap_or_default();
    conn.execute(
        "INSERT INTO sandbox_overrides
           (peer_name, allow_network, allow_disk_write, max_cpu_seconds,
            max_memory_mb, allowed_commands, blocked_paths)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
         ON CONFLICT(peer_name) DO UPDATE SET
           allow_network    = excluded.allow_network,
           allow_disk_write = excluded.allow_disk_write,
           max_cpu_seconds  = excluded.max_cpu_seconds,
           max_memory_mb    = excluded.max_memory_mb,
           allowed_commands = excluded.allowed_commands,
           blocked_paths    = excluded.blocked_paths",
        rusqlite::params![
            policy.peer_name,
            policy.allow_network as i64,
            policy.allow_disk_write as i64,
            policy.max_cpu_seconds as i64,
            policy.max_memory_mb as i64,
            cmds,
            paths,
        ],
    )?;
    Ok(())
}

/// Resolve effective sandbox: custom override if present, else trust-based default.
pub fn resolve_sandbox(conn: &Connection, peer: &str, trust: TrustLevel) -> SandboxPolicy {
    get_custom_sandbox(conn, peer).unwrap_or_else(|| sandbox_for_trust(peer, trust))
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
    fn test_sandbox_for_trust_untrusted() {
        let policy = sandbox_for_trust("rogue-peer", TrustLevel::Untrusted);
        assert!(!policy.allow_network);
        assert!(!policy.allow_disk_write);
        assert_eq!(policy.max_cpu_seconds, 60);
        assert_eq!(policy.max_memory_mb, 512);
        assert!(policy.allowed_commands.is_empty());
    }

    #[test]
    fn test_sandbox_for_trust_owner() {
        let policy = sandbox_for_trust("owner-node", TrustLevel::Owner);
        assert!(policy.allow_network);
        assert!(policy.allow_disk_write);
        assert_eq!(policy.max_cpu_seconds, 0);
        assert_eq!(policy.max_memory_mb, 0);
    }

    #[test]
    fn test_custom_sandbox_roundtrip() {
        let conn = setup_db();
        let policy = SandboxPolicy {
            peer_name: "custom-peer".into(),
            allow_network: true,
            allow_disk_write: false,
            max_cpu_seconds: 120,
            max_memory_mb: 2048,
            allowed_commands: vec!["cargo".into()],
            blocked_paths: vec!["/tmp/forbidden".into()],
        };
        set_custom_sandbox(&conn, &policy).unwrap();
        let loaded = get_custom_sandbox(&conn, "custom-peer").unwrap();
        assert_eq!(loaded.max_cpu_seconds, 120);
        assert!(loaded.allow_network);
        assert!(!loaded.allow_disk_write);
    }
}
