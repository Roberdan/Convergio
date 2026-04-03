// DB migrations for evidence tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "task evidence recording",
            up: "
                CREATE TABLE IF NOT EXISTS task_evidence (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_db_id     INTEGER NOT NULL,
                    evidence_type  TEXT    NOT NULL,
                    command        TEXT    NOT NULL DEFAULT '',
                    output_summary TEXT    NOT NULL DEFAULT '',
                    exit_code      INTEGER NOT NULL DEFAULT 0,
                    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_task_evidence_task
                    ON task_evidence(task_db_id, evidence_type);
            ",
        },
        Migration {
            version: 2,
            description: "commit-to-task matching",
            up: "
                CREATE TABLE IF NOT EXISTS commit_task_matches (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id        INTEGER NOT NULL,
                    commit_hash    TEXT    NOT NULL,
                    commit_message TEXT    NOT NULL DEFAULT '',
                    matched_at     TEXT    NOT NULL DEFAULT (datetime('now')),
                    UNIQUE(task_id, commit_hash)
                );
            ",
        },
        Migration {
            version: 3,
            description: "stale task notifications",
            up: "
                CREATE TABLE IF NOT EXISTS stale_task_notifications (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id     INTEGER NOT NULL,
                    reason      TEXT    NOT NULL,
                    notified_at TEXT    NOT NULL DEFAULT (datetime('now')),
                    resolved    INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(task_id, reason)
                );
            ",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_are_ordered() {
        let m = migrations();
        for (i, mig) in m.iter().enumerate() {
            assert_eq!(mig.version, (i + 1) as u32);
        }
    }

    #[test]
    fn migrations_apply_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        // Evidence needs orchestrator tables (tasks FK)
        let orch_applied = convergio_db::migration::apply_migrations(
            &conn,
            "orchestrator",
            &convergio_orchestrator::schema::migrations(),
        )
        .unwrap();
        assert_eq!(orch_applied, 3);
        let applied =
            convergio_db::migration::apply_migrations(&conn, "evidence", &migrations()).unwrap();
        assert_eq!(applied, 3);
    }
}
