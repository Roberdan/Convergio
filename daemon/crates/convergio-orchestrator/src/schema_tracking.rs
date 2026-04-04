//! Migration v4 — Plan protocol tracking tables.
//!
//! Adds: token_usage, agent_activity, plan_metadata, delegation_log.
//! Also adds timestamp columns to plans, tasks, waves.

use convergio_types::extension::Migration;

pub fn tracking_migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 4,
            description: "token usage tracking",
            up: "CREATE TABLE IF NOT EXISTS token_usage (\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    plan_id INTEGER REFERENCES plans(id),\
                    wave_id INTEGER,\
                    task_id INTEGER,\
                    agent TEXT NOT NULL,\
                    model TEXT NOT NULL,\
                    input_tokens INTEGER NOT NULL DEFAULT 0,\
                    output_tokens INTEGER NOT NULL DEFAULT 0,\
                    cost_usd REAL NOT NULL DEFAULT 0.0,\
                    execution_host TEXT,\
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))\
                );\
                CREATE INDEX IF NOT EXISTS idx_tu_plan ON token_usage(plan_id);\
                CREATE INDEX IF NOT EXISTS idx_tu_agent ON token_usage(agent);\
                CREATE INDEX IF NOT EXISTS idx_tu_model ON token_usage(model);\
                CREATE INDEX IF NOT EXISTS idx_tu_created ON token_usage(created_at);",
        },
        Migration {
            version: 5,
            description: "agent activity tracking",
            up: "CREATE TABLE IF NOT EXISTS agent_activity (\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    agent_id TEXT NOT NULL,\
                    agent_type TEXT,\
                    plan_id INTEGER REFERENCES plans(id),\
                    task_id INTEGER,\
                    action TEXT NOT NULL,\
                    status TEXT NOT NULL DEFAULT 'started',\
                    model TEXT,\
                    tokens_in INTEGER NOT NULL DEFAULT 0,\
                    tokens_out INTEGER NOT NULL DEFAULT 0,\
                    cost_usd REAL NOT NULL DEFAULT 0.0,\
                    started_at TEXT NOT NULL DEFAULT (datetime('now')),\
                    completed_at TEXT,\
                    duration_s REAL,\
                    host TEXT,\
                    exit_reason TEXT,\
                    metadata_json TEXT,\
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))\
                );\
                CREATE INDEX IF NOT EXISTS idx_aa_agent ON agent_activity(agent_id);\
                CREATE INDEX IF NOT EXISTS idx_aa_plan ON agent_activity(plan_id);\
                CREATE INDEX IF NOT EXISTS idx_aa_status ON agent_activity(status);",
        },
        Migration {
            version: 6,
            description: "plan metadata and delegation log",
            up: "CREATE TABLE IF NOT EXISTS plan_metadata (\
                    plan_id INTEGER PRIMARY KEY REFERENCES plans(id),\
                    objective TEXT,\
                    motivation TEXT,\
                    requester TEXT,\
                    created_by TEXT,\
                    approved_by TEXT,\
                    key_learnings_json TEXT,\
                    report_json TEXT,\
                    closed_at TEXT\
                );\
                CREATE TABLE IF NOT EXISTS delegation_log (\
                    id INTEGER PRIMARY KEY AUTOINCREMENT,\
                    plan_id INTEGER REFERENCES plans(id),\
                    task_id INTEGER,\
                    peer_name TEXT,\
                    agent TEXT,\
                    delegated_at TEXT NOT NULL DEFAULT (datetime('now')),\
                    completed_at TEXT,\
                    status TEXT NOT NULL DEFAULT 'pending',\
                    cost_usd REAL NOT NULL DEFAULT 0.0,\
                    tokens_total INTEGER NOT NULL DEFAULT 0\
                );\
                CREATE INDEX IF NOT EXISTS idx_dl_plan ON delegation_log(plan_id);\
                CREATE INDEX IF NOT EXISTS idx_dl_status ON delegation_log(status);",
        },
        Migration {
            version: 7,
            description: "add timestamp columns to plans, tasks, waves",
            up: "ALTER TABLE plans ADD COLUMN started_at TEXT;\
                 ALTER TABLE plans ADD COLUMN completed_at TEXT;\
                 ALTER TABLE plans ADD COLUMN cancelled_at TEXT;\
                 ALTER TABLE tasks ADD COLUMN validated_at TEXT;\
                 ALTER TABLE tasks ADD COLUMN validator_agent TEXT;\
                 ALTER TABLE tasks ADD COLUMN duration_minutes REAL;\
                 ALTER TABLE waves ADD COLUMN completed_at TEXT;\
                 ALTER TABLE waves ADD COLUMN cancelled_at TEXT;",
        },
        Migration {
            version: 8,
            description: "artifact storage for non-code projects",
            up: "CREATE TABLE IF NOT EXISTS artifacts (\
                     id            INTEGER PRIMARY KEY AUTOINCREMENT,\
                     task_id       INTEGER NOT NULL,\
                     plan_id       INTEGER NOT NULL,\
                     name          TEXT NOT NULL,\
                     artifact_type TEXT NOT NULL DEFAULT 'document',\
                     path          TEXT NOT NULL,\
                     size_bytes    INTEGER NOT NULL DEFAULT 0,\
                     created_at    TEXT NOT NULL DEFAULT (datetime('now'))\
                 );\
                 CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);\
                 CREATE INDEX IF NOT EXISTS idx_artifacts_plan ON artifacts(plan_id);\
                 CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);",
        },
        Migration {
            version: 9,
            description: "artifact metadata: mime_type and content_hash",
            up: "ALTER TABLE artifacts ADD COLUMN mime_type TEXT \
                     DEFAULT 'application/octet-stream';\
                 ALTER TABLE artifacts ADD COLUMN content_hash TEXT;",
        },
        Migration {
            version: 10,
            description: "artifact bundles for grouped deliverables",
            up: "CREATE TABLE IF NOT EXISTS artifact_bundles (\
                     id           INTEGER PRIMARY KEY AUTOINCREMENT,\
                     plan_id      INTEGER NOT NULL,\
                     name         TEXT NOT NULL,\
                     bundle_type  TEXT NOT NULL DEFAULT 'deliverable',\
                     status       TEXT NOT NULL DEFAULT 'draft',\
                     created_at   TEXT NOT NULL DEFAULT (datetime('now')),\
                     published_at TEXT\
                 );\
                 CREATE TABLE IF NOT EXISTS bundle_artifacts (\
                     bundle_id   INTEGER NOT NULL,\
                     artifact_id INTEGER NOT NULL,\
                     added_at    TEXT NOT NULL DEFAULT (datetime('now')),\
                     PRIMARY KEY (bundle_id, artifact_id)\
                 );\
                 CREATE INDEX IF NOT EXISTS idx_bundles_plan \
                     ON artifact_bundles(plan_id);\
                 CREATE INDEX IF NOT EXISTS idx_bundles_status \
                     ON artifact_bundles(status);",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tracking_migrations_apply_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        // Apply base migrations first
        let base = crate::schema::migrations();
        convergio_db::migration::apply_migrations(&conn, "orchestrator", &base).unwrap();
        // Apply tracking migrations
        let tracking = tracking_migrations();
        let applied =
            convergio_db::migration::apply_migrations(&conn, "orchestrator", &tracking).unwrap();
        assert_eq!(applied, 7);
    }
}
