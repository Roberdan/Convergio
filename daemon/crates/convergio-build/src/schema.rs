//! DB migrations for the build module.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "build history tracking table",
        up: "\
CREATE TABLE IF NOT EXISTS build_history (
    id            TEXT PRIMARY KEY,
    status        TEXT NOT NULL DEFAULT 'queued',
    commit_hash   TEXT NOT NULL,
    test_count    INTEGER,
    binary_hash   TEXT,
    binary_size   INTEGER,
    started_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT,
    error         TEXT,
    duration_secs REAL
);
CREATE INDEX IF NOT EXISTS idx_build_history_date
    ON build_history(started_at);
CREATE INDEX IF NOT EXISTS idx_build_history_status
    ON build_history(status);",
    }]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_apply_to_sqlite() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' \
                 AND name = 'build_history'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn migrations_have_sequential_versions() {
        let migs = migrations();
        for (i, m) in migs.iter().enumerate() {
            assert_eq!(m.version, (i + 1) as u32);
        }
    }
}
