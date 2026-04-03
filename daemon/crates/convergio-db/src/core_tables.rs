//! Core database tables owned by convergio-db.
//!
//! _schema_registry — managed by migration runner
//! _sync_meta — last sync timestamp per peer+table
//! _sync_conflicts — recorded merge conflicts

use convergio_types::extension::Migration;

/// Core migrations for convergio-db owned tables.
pub fn core_migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "sync metadata tracking",
            up: "CREATE TABLE IF NOT EXISTS _sync_meta (
                peer TEXT NOT NULL,
                table_name TEXT NOT NULL,
                last_synced TEXT NOT NULL,
                PRIMARY KEY (peer, table_name)
            )",
        },
        Migration {
            version: 2,
            description: "sync conflict log",
            up: "CREATE TABLE IF NOT EXISTS _sync_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                pk TEXT NOT NULL,
                local_data TEXT,
                remote_data TEXT,
                resolved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::migration::apply_migrations;
    use rusqlite::Connection;

    #[test]
    fn core_migrations_apply() {
        let conn = Connection::open_in_memory().unwrap();
        let migrations = core_migrations();
        let applied = apply_migrations(&conn, "convergio-db", &migrations).unwrap();
        assert_eq!(applied, 2);

        // Verify tables exist
        let sync_meta: bool = conn
            .query_row(
                "SELECT COUNT(*) > 0 FROM sqlite_master WHERE name = '_sync_meta'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert!(sync_meta);
    }
}
