//! DB migrations for the file-transport module.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "file_transfers tracking table",
        up: "\
CREATE TABLE IF NOT EXISTS file_transfers (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_name          TEXT NOT NULL,
    direction          TEXT NOT NULL,
    source_path        TEXT NOT NULL,
    dest_path          TEXT NOT NULL,
    bytes_transferred  INTEGER DEFAULT 0,
    files_count        INTEGER DEFAULT 0,
    duration_ms        INTEGER DEFAULT 0,
    status             TEXT NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ft_peer_date
    ON file_transfers(peer_name, created_at);",
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
        // Verify table exists
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='table' AND name='file_transfers'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn index_exists_after_migration() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='index' AND name='idx_ft_peer_date'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }
}
