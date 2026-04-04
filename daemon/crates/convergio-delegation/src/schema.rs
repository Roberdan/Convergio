//! DB migrations for the delegation module.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "delegations tracking table",
        up: "\
CREATE TABLE IF NOT EXISTS delegations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    delegation_id   TEXT NOT NULL UNIQUE,
    plan_id         INTEGER NOT NULL,
    peer_name       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    current_step    TEXT NOT NULL DEFAULT 'init',
    source_path     TEXT,
    remote_path     TEXT,
    error_message   TEXT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_delegations_plan ON delegations(plan_id);
CREATE INDEX IF NOT EXISTS idx_delegations_peer ON delegations(peer_name);
CREATE INDEX IF NOT EXISTS idx_delegations_status ON delegations(status);",
    }]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_are_ordered() {
        let migs = migrations();
        assert!(!migs.is_empty());
        for (i, m) in migs.iter().enumerate() {
            assert_eq!(m.version, (i + 1) as u32);
        }
    }

    #[test]
    fn migrations_apply_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='table' AND name='delegations'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn indexes_exist_after_migration() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='index' AND name LIKE 'idx_delegations_%'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 3);
    }
}
