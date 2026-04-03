// DB migrations for orchestrator tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "core orchestrator tables",
            up: "
                CREATE TABLE IF NOT EXISTS projects (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    description TEXT,
                    output_path TEXT,
                    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS plans (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id       TEXT    NOT NULL,
                    name             TEXT    NOT NULL,
                    status           TEXT    NOT NULL DEFAULT 'todo',
                    tasks_done       INTEGER NOT NULL DEFAULT 0,
                    tasks_total      INTEGER NOT NULL DEFAULT 0,
                    depends_on       TEXT,
                    execution_mode   TEXT,
                    is_master        INTEGER NOT NULL DEFAULT 0,
                    parent_plan_id   INTEGER,
                    execution_host   TEXT,
                    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS waves (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    wave_id    TEXT    NOT NULL,
                    plan_id    INTEGER NOT NULL,
                    name       TEXT    NOT NULL DEFAULT '',
                    status     TEXT    NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    FOREIGN KEY (plan_id) REFERENCES plans(id)
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id        TEXT,
                    plan_id        INTEGER NOT NULL,
                    wave_id        INTEGER,
                    title          TEXT    NOT NULL DEFAULT '',
                    description    TEXT,
                    status         TEXT    NOT NULL DEFAULT 'pending',
                    executor_agent TEXT,
                    started_at     TEXT,
                    completed_at   TEXT,
                    notes          TEXT,
                    tokens         INTEGER,
                    output_data    TEXT,
                    executor_host  TEXT,
                    FOREIGN KEY (plan_id) REFERENCES plans(id),
                    FOREIGN KEY (wave_id) REFERENCES waves(id)
                );
            ",
        },
        Migration {
            version: 2,
            description: "validation queue, verdicts, audit log",
            up: "
                CREATE TABLE IF NOT EXISTS validation_queue (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id      INTEGER,
                    wave_id      INTEGER,
                    plan_id      INTEGER,
                    status       TEXT    NOT NULL DEFAULT 'pending',
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                    started_at   TEXT,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS validation_verdicts (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    queue_id   INTEGER NOT NULL,
                    verdict    TEXT    NOT NULL,
                    report     TEXT,
                    validator  TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    action      TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id   INTEGER,
                    actor       TEXT,
                    details     TEXT,
                    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
                );
            ",
        },
        Migration {
            version: 3,
            description: "execution policy, rollback, approval",
            up: "
                CREATE TABLE IF NOT EXISTS execution_policy (
                    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id                TEXT    NOT NULL,
                    risk_level                TEXT    NOT NULL,
                    auto_progress             INTEGER NOT NULL DEFAULT 1,
                    require_human             INTEGER NOT NULL DEFAULT 0,
                    require_double_validation INTEGER NOT NULL DEFAULT 0,
                    UNIQUE (project_id, risk_level)
                );

                CREATE TABLE IF NOT EXISTS rollback_snapshots (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id       INTEGER,
                    git_ref       TEXT NOT NULL,
                    changed_files TEXT,
                    db_rows_json  TEXT,
                    created_at    TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS approval_cache (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    reason_code TEXT NOT NULL,
                    task_type   TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    created_at  TEXT DEFAULT (datetime('now')),
                    UNIQUE (reason_code, task_type)
                );

                CREATE TABLE IF NOT EXISTS batch_approvals (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id     TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    created_at  TEXT DEFAULT (datetime('now')),
                    UNIQUE (task_id)
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
        let applied = convergio_db::migration::apply_migrations(
            &conn, "orchestrator", &migrations(),
        ).unwrap();
        assert_eq!(applied, 3);
    }
}
