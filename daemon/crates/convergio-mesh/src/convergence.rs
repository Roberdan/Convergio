//! Post-sync convergence verification.
//!
//! After each sync round, record local state checksum in mesh_peer_state
//! and warn if any known peer has diverged for more than 5 minutes.

use rusqlite::Connection;
use sha2::{Digest, Sha256};
use tracing::warn;

/// Convergence drift threshold in seconds.
const DRIFT_THRESHOLD_SECS: i64 = 300;

/// Compute SHA-256 checksum from key DB table counts and statuses.
/// Hashes: plan count+statuses, task count+statuses, wave count+statuses.
/// Tables that don't exist yet are silently skipped.
pub fn compute_local_checksum(conn: &Connection) -> String {
    let mut hasher = Sha256::new();

    let tables = &[
        ("plans", "SELECT status, COUNT(*) as c FROM plans GROUP BY status ORDER BY status"),
        ("tasks", "SELECT status, COUNT(*) as c FROM tasks GROUP BY status ORDER BY status"),
        ("waves", "SELECT status, COUNT(*) as c FROM waves GROUP BY status ORDER BY status"),
    ];

    for (table, sql) in tables {
        hasher.update(table.as_bytes());
        hasher.update(b":");
        if let Ok(mut stmt) = conn.prepare(sql) {
            if let Ok(rows) = stmt.query_map([], |row| {
                Ok((
                    row.get::<_, String>(0).unwrap_or_default(),
                    row.get::<_, i64>(1).unwrap_or(0),
                ))
            }) {
                for row in rows.flatten() {
                    hasher.update(format!("{}={};", row.0, row.1).as_bytes());
                }
            }
        }
        hasher.update(b"|");
    }

    hasher
        .finalize()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

/// Check convergence after a sync round: upsert local state checksum in
/// mesh_peer_state, warn on diverged peers (>5 min different checksum).
pub fn check_convergence(conn: &Connection) {
    let local_checksum = compute_local_checksum(conn);

    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_else(|_| "unknown".to_string());

    if let Err(e) = conn.execute(
        "INSERT INTO mesh_peer_state (peer_id, state_version, state_checksum, last_seen)
         VALUES (?1, 1, ?2, datetime('now'))
         ON CONFLICT(peer_id) DO UPDATE SET
             state_version = state_version + 1,
             state_checksum = excluded.state_checksum,
             last_seen = excluded.last_seen",
        rusqlite::params![hostname, local_checksum],
    ) {
        warn!("convergence: upsert local state for '{hostname}': {e}");
        return;
    }

    let query = "SELECT peer_id, state_checksum,
                        CAST((julianday('now') - julianday(last_seen)) * 86400 AS INTEGER)
                            AS age_secs
                 FROM mesh_peer_state
                 WHERE peer_id != ?1
                   AND state_checksum != ?2
                   AND (julianday('now') - julianday(last_seen)) * 86400 > ?3";

    let Ok(mut stmt) = conn.prepare(query) else {
        warn!("convergence: failed to prepare divergence query");
        return;
    };

    let rows = stmt.query_map(
        rusqlite::params![hostname, local_checksum, DRIFT_THRESHOLD_SECS],
        |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, i64>(2)?,
            ))
        },
    );
    if let Ok(iter) = rows {
        for row in iter.flatten() {
            warn!(
                "convergence: peer '{}' diverged for {}s \
                 (theirs: {}, ours: {})",
                row.0, row.2, row.1, local_checksum
            );
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE plans (id INTEGER PRIMARY KEY, status TEXT);
             CREATE TABLE tasks (id INTEGER PRIMARY KEY, status TEXT);
             CREATE TABLE waves (id INTEGER PRIMARY KEY, status TEXT);
             CREATE TABLE mesh_peer_state (
                 peer_id TEXT PRIMARY KEY,
                 state_version INTEGER NOT NULL DEFAULT 0,
                 state_checksum TEXT NOT NULL DEFAULT '',
                 last_seen TEXT NOT NULL DEFAULT (datetime('now'))
             );",
        )
        .unwrap();
        conn
    }

    #[test]
    fn checksum_deterministic() {
        let conn = setup_db();
        let c1 = compute_local_checksum(&conn);
        let c2 = compute_local_checksum(&conn);
        assert_eq!(c1, c2);
        assert_eq!(c1.len(), 64);
    }

    #[test]
    fn checksum_changes_with_data() {
        let conn = setup_db();
        let before = compute_local_checksum(&conn);
        conn.execute("INSERT INTO plans (status) VALUES ('doing')", [])
            .unwrap();
        let after = compute_local_checksum(&conn);
        assert_ne!(before, after);
    }

    #[test]
    fn convergence_inserts_local_state() {
        let conn = setup_db();
        check_convergence(&conn);
        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM mesh_peer_state", [], |r| r.get(0))
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn convergence_increments_version() {
        let conn = setup_db();
        check_convergence(&conn);
        check_convergence(&conn);
        let version: i64 = conn
            .query_row(
                "SELECT state_version FROM mesh_peer_state LIMIT 1",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(version, 2);
    }

    #[test]
    fn checksum_degrades_without_tables() {
        let conn = Connection::open_in_memory().unwrap();
        let checksum = compute_local_checksum(&conn);
        assert_eq!(checksum.len(), 64);
    }
}
