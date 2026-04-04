//! Mesh DB migrations: peer heartbeats, sync stats, convergence,
//! coordinator events, delegation progress.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "core mesh tables",
            up: "
CREATE TABLE IF NOT EXISTS mesh_sync_stats (
    peer_name           TEXT PRIMARY KEY,
    total_sent          INTEGER NOT NULL DEFAULT 0,
    total_received      INTEGER NOT NULL DEFAULT 0,
    total_applied       INTEGER NOT NULL DEFAULT 0,
    last_sent_at        TEXT,
    last_sync_at        TEXT,
    last_latency_ms     INTEGER,
    last_db_version     INTEGER,
    last_error          TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    status              TEXT NOT NULL DEFAULT 'unknown'
);

CREATE TABLE IF NOT EXISTS peer_heartbeats (
    peer_name       TEXT PRIMARY KEY,
    last_seen       INTEGER NOT NULL DEFAULT (unixepoch()),
    load_json       TEXT,
    capabilities    TEXT,
    version         TEXT,
    rustc_version   TEXT
);

CREATE TABLE IF NOT EXISTS host_heartbeats (
    hostname    TEXT PRIMARY KEY,
    last_seen   INTEGER NOT NULL DEFAULT (unixepoch()),
    status      TEXT NOT NULL DEFAULT 'online',
    metadata    TEXT
);

CREATE TABLE IF NOT EXISTS mesh_peer_state (
    peer_id         TEXT PRIMARY KEY,
    state_version   INTEGER NOT NULL DEFAULT 0,
    state_checksum  TEXT NOT NULL DEFAULT '',
    last_seen       TEXT NOT NULL DEFAULT (datetime('now'))
);
",
        },
        Migration {
            version: 2,
            description: "coordinator events and delegation progress",
            up: "
CREATE TABLE IF NOT EXISTS coordinator_events (
    id          INTEGER PRIMARY KEY,
    event_type  TEXT NOT NULL,
    payload     TEXT,
    source_node TEXT,
    handled_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_coord_events_type
    ON coordinator_events(event_type);

CREATE TABLE IF NOT EXISTS delegation_progress (
    id              INTEGER PRIMARY KEY,
    delegation_id   TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'running',
    current_task    TEXT,
    output_summary  TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_delegation_id
    ON delegation_progress(delegation_id);
",
        },
        Migration {
            version: 3,
            description: "node capability registry",
            up: "
CREATE TABLE IF NOT EXISTS node_capabilities (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_name           TEXT NOT NULL,
    capability_name     TEXT NOT NULL,
    capability_version  TEXT NOT NULL DEFAULT '1.0.0',
    tags_json           TEXT NOT NULL DEFAULT '[]',
    metadata_json       TEXT NOT NULL DEFAULT '{}',
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(peer_name, capability_name)
);
CREATE INDEX IF NOT EXISTS idx_node_cap_peer
    ON node_capabilities(peer_name);
CREATE INDEX IF NOT EXISTS idx_node_cap_name
    ON node_capabilities(capability_name);
",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    #[test]
    fn migrations_apply_cleanly() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        let applied = convergio_db::migration::apply_migrations(&conn, "mesh", &migrations());
        assert_eq!(applied.unwrap(), 3);
    }

    #[test]
    fn migrations_are_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "mesh", &migrations()).unwrap();
        let applied = convergio_db::migration::apply_migrations(&conn, "mesh", &migrations());
        assert_eq!(applied.unwrap(), 0);
    }

    #[test]
    fn heartbeat_upsert() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "mesh", &migrations()).unwrap();
        conn.execute(
            "INSERT INTO peer_heartbeats (peer_name) VALUES ('M5Max')
             ON CONFLICT(peer_name) DO UPDATE SET last_seen = unixepoch()",
            [],
        )
        .unwrap();
        let count: i64 = conn
            .query_row("SELECT count(*) FROM peer_heartbeats", [], |r| r.get(0))
            .unwrap();
        assert_eq!(count, 1);
    }
}
