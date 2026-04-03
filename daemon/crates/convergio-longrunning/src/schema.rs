//! DB migrations for the long-running execution protocol.
//!
//! Tables: lr_executions, lr_checkpoints, lr_heartbeats, lr_delegations.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "long-running executions table",
            up: "\
CREATE TABLE IF NOT EXISTS lr_executions (
    id          TEXT PRIMARY KEY,
    agent       TEXT NOT NULL,
    node        TEXT NOT NULL,
    parent_id   TEXT,
    stage       TEXT NOT NULL DEFAULT 'starting',
    budget_usd  REAL NOT NULL DEFAULT 0.0,
    spent_usd   REAL NOT NULL DEFAULT 0.0,
    deadline    TEXT,
    percent     REAL NOT NULL DEFAULT 0.0,
    message     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_lr_exec_stage ON lr_executions(stage);
CREATE INDEX IF NOT EXISTS idx_lr_exec_parent ON lr_executions(parent_id);",
        },
        Migration {
            version: 2,
            description: "checkpoint persistence table",
            up: "\
CREATE TABLE IF NOT EXISTS lr_checkpoints (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    state        TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (execution_id) REFERENCES lr_executions(id)
);
CREATE INDEX IF NOT EXISTS idx_lr_ckpt_exec ON lr_checkpoints(execution_id);",
        },
        Migration {
            version: 3,
            description: "heartbeat tracking table",
            up: "\
CREATE TABLE IF NOT EXISTS lr_heartbeats (
    execution_id TEXT PRIMARY KEY,
    last_seen    TEXT NOT NULL DEFAULT (datetime('now')),
    interval_s   INTEGER NOT NULL DEFAULT 30,
    FOREIGN KEY (execution_id) REFERENCES lr_executions(id)
);",
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
        // Verify tables exist
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' \
                 AND name LIKE 'lr_%'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 3);
    }
}
