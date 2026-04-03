//! DB migrations for the backup module.
//!
//! Tables: backup_snapshots, backup_retention_rules, backup_purge_log.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "snapshot tracking table",
            up: "\
CREATE TABLE IF NOT EXISTS backup_snapshots (
    id          TEXT PRIMARY KEY,
    path        TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    checksum    TEXT NOT NULL,
    node        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_backup_snap_date
    ON backup_snapshots(created_at);",
        },
        Migration {
            version: 2,
            description: "retention rules and purge log tables",
            up: "\
CREATE TABLE IF NOT EXISTS backup_retention_rules (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name        TEXT NOT NULL,
    timestamp_column  TEXT NOT NULL DEFAULT 'created_at',
    max_age_days      INTEGER NOT NULL,
    org_id            TEXT NOT NULL DEFAULT '__global__',
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(table_name, org_id)
);
CREATE TABLE IF NOT EXISTS backup_purge_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name    TEXT NOT NULL,
    rows_deleted  INTEGER NOT NULL,
    cutoff_date   TEXT NOT NULL,
    executed_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_purge_log_date
    ON backup_purge_log(executed_at);",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_have_sequential_versions() {
        let migs = migrations();
        assert!(!migs.is_empty());
        for (i, m) in migs.iter().enumerate() {
            assert_eq!(m.version, (i + 1) as u32);
        }
    }

    #[test]
    fn migrations_apply_to_sqlite() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' \
                 AND name LIKE 'backup_%'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 3);
    }

    #[test]
    fn retention_rules_table_has_unique_constraint() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute(
            "INSERT INTO backup_retention_rules \
             (table_name, max_age_days, org_id) \
             VALUES ('audit_log', 365, '__global__')",
            [],
        )
        .unwrap();
        // Duplicate with same org_id should fail
        let result = conn.execute(
            "INSERT INTO backup_retention_rules \
             (table_name, max_age_days, org_id) \
             VALUES ('audit_log', 30, '__global__')",
            [],
        );
        assert!(result.is_err());
    }
}
