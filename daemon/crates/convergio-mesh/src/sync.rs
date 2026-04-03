//! HTTP LWW sync loop: timestamp-based peer replication.
//!
//! Migrated from background_sync.rs in the old monolite.
//! Includes schema version guard: rejects sync from peers with
//! different schema versions to prevent data corruption.

use rusqlite::Connection;
use std::time::Duration;
use tracing::{error, warn};

use crate::sync_apply::{apply_changes, export_changes_since};
use crate::transport::{fetch_changes_from_peer, send_changes_to_peer};
use crate::types::{SyncMeta, DEFAULT_INTERVAL_SECS};

/// Resolve sync interval: explicit arg > env var > 30s default.
pub fn resolve_interval_secs(override_secs: Option<u64>) -> u64 {
    if let Some(v) = override_secs {
        return v;
    }
    match std::env::var("CONVERGIO_SYNC_INTERVAL_SECS") {
        Ok(s) => s.parse().unwrap_or(DEFAULT_INTERVAL_SECS),
        Err(_) => DEFAULT_INTERVAL_SECS,
    }
}

/// Check if local and peer schema versions match for all modules.
/// Returns Ok(()) if compatible, Err with details if mismatch.
pub fn check_schema_compatibility(conn: &Connection, peer_addr: &str) -> Result<(), String> {
    let local_versions = local_schema_versions(conn);
    if local_versions.is_empty() {
        return Ok(());
    }
    let client = reqwest::blocking::Client::builder()
        .connect_timeout(Duration::from_secs(3))
        .timeout(Duration::from_secs(5))
        .build()
        .map_err(|e| format!("HTTP client: {e}"))?;
    let url = format!("http://{peer_addr}/api/health");
    let resp = client.get(&url).send().map_err(|e| e.to_string())?;
    if !resp.status().is_success() {
        return Err(format!("health endpoint returned {}", resp.status()));
    }
    let body: serde_json::Value = resp.json().map_err(|e| format!("parse: {e}"))?;
    let Some(remote) = body.get("schema_versions").and_then(|v| v.as_object()) else {
        return Ok(());
    };
    for (module, local_ver) in &local_versions {
        if let Some(remote_ver) = remote.get(module).and_then(|v| v.as_u64()) {
            if remote_ver as u32 != *local_ver {
                return Err(format!(
                    "schema mismatch for '{module}': local={local_ver}, \
                     peer({peer_addr})={remote_ver} — peer must upgrade"
                ));
            }
        }
    }
    Ok(())
}

fn local_schema_versions(conn: &Connection) -> Vec<(String, u32)> {
    let mut stmt = match conn.prepare("SELECT module, version FROM _schema_registry") {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map([], |row| {
        Ok((row.get::<_, String>(0)?, row.get::<_, u32>(1)?))
    })
    .map(|rows| rows.flatten().collect())
    .unwrap_or_default()
}

/// Upsert sync metadata for a peer+table pair.
pub fn upsert_sync_meta(conn: &Connection, meta: &SyncMeta) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO _sync_meta (peer, table_name, last_synced) \
         VALUES (?1, ?2, ?3) \
         ON CONFLICT (peer, table_name) \
         DO UPDATE SET last_synced = excluded.last_synced",
        rusqlite::params![meta.peer, meta.table_name, meta.last_synced],
    )?;
    Ok(())
}

/// Get sync metadata for a peer+table pair.
pub fn get_sync_meta(
    conn: &Connection,
    peer: &str,
    table_name: &str,
) -> rusqlite::Result<Option<SyncMeta>> {
    use rusqlite::OptionalExtension;
    conn.query_row(
        "SELECT peer, table_name, last_synced FROM _sync_meta \
         WHERE peer = ?1 AND table_name = ?2",
        rusqlite::params![peer, table_name],
        |row| {
            Ok(SyncMeta {
                peer: row.get(0)?,
                table_name: row.get(1)?,
                last_synced: row.get(2)?,
            })
        },
    )
    .optional()
}

/// Sync one table with a peer. Returns (sent, received, applied).
pub fn sync_table_with_peer(
    conn: &Connection,
    peer_addr: &str,
    table: &str,
) -> (usize, usize, usize) {
    let since = get_sync_meta(conn, peer_addr, table)
        .ok()
        .flatten()
        .map(|m| m.last_synced);

    let local_changes = match export_changes_since(conn, table, since.as_deref()) {
        Ok(c) => c,
        Err(e) => {
            warn!(peer = %peer_addr, table, error = %e, "export failed");
            return (0, 0, 0);
        }
    };

    if !local_changes.is_empty() {
        if let Err(e) = send_changes_to_peer(peer_addr, &local_changes) {
            error!(peer = %peer_addr, error = %e, "send changes failed");
            return (0, 0, 0);
        }
    }

    let remote_changes = match fetch_changes_from_peer(peer_addr, table, since.as_deref()) {
        Ok(c) => c,
        Err(e) => {
            warn!(peer = %peer_addr, table, error = %e, "fetch failed");
            return (0, 0, 0);
        }
    };

    let applied = match apply_changes(conn, &remote_changes) {
        Ok(n) => n,
        Err(e) => {
            warn!(peer = %peer_addr, table, error = %e, "apply failed");
            return (0, 0, 0);
        }
    };

    let now = chrono::Utc::now().format("%Y-%m-%d %H:%M:%S").to_string();
    let meta = SyncMeta {
        peer: peer_addr.to_string(),
        table_name: table.to_string(),
        last_synced: now,
    };
    if let Err(e) = upsert_sync_meta(conn, &meta) {
        warn!(peer = %peer_addr, table, error = %e, "upsert meta failed");
    }

    (local_changes.len(), remote_changes.len(), applied)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resolve_interval_default() {
        assert_eq!(resolve_interval_secs(None), DEFAULT_INTERVAL_SECS);
    }

    #[test]
    fn resolve_interval_override() {
        assert_eq!(resolve_interval_secs(Some(10)), 10);
    }

    #[test]
    fn schema_versions_empty_db() {
        let conn = Connection::open_in_memory().unwrap();
        let versions = local_schema_versions(&conn);
        assert!(versions.is_empty());
    }

    #[test]
    fn sync_meta_roundtrip() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::core_tables::core_migrations()
            .iter()
            .for_each(|m| {
                conn.execute_batch(m.up).unwrap();
            });
        let meta = SyncMeta {
            peer: "peer1".into(),
            table_name: "plans".into(),
            last_synced: "2026-04-03 12:00:00".into(),
        };
        upsert_sync_meta(&conn, &meta).unwrap();
        let got = get_sync_meta(&conn, "peer1", "plans").unwrap().unwrap();
        assert_eq!(got.last_synced, "2026-04-03 12:00:00");
    }
}
