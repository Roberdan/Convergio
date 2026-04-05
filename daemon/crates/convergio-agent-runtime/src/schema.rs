//! DB migrations for the agent runtime.
//!
//! Tables: art_agents, art_heartbeats, art_delegations, art_queue,
//! art_scope_rules, art_context.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "agent runtime core tables",
            up: "\
CREATE TABLE IF NOT EXISTS art_agents (
    id              TEXT PRIMARY KEY,
    agent_name      TEXT NOT NULL,
    org_id          TEXT NOT NULL,
    task_id         INTEGER,
    stage           TEXT NOT NULL DEFAULT 'spawning',
    workspace_path  TEXT,
    model           TEXT,
    node            TEXT NOT NULL,
    budget_usd      REAL NOT NULL DEFAULT 0.0,
    spent_usd       REAL NOT NULL DEFAULT 0.0,
    priority        INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_art_agents_org ON art_agents(org_id);
CREATE INDEX IF NOT EXISTS idx_art_agents_stage ON art_agents(stage);
CREATE INDEX IF NOT EXISTS idx_art_agents_task ON art_agents(task_id);

CREATE TABLE IF NOT EXISTS art_heartbeats (
    agent_id    TEXT PRIMARY KEY,
    last_seen   TEXT NOT NULL DEFAULT (datetime('now')),
    interval_s  INTEGER NOT NULL DEFAULT 30,
    FOREIGN KEY (agent_id) REFERENCES art_agents(id)
);",
        },
        Migration {
            version: 2,
            description: "delegation and scheduling tables",
            up: "\
CREATE TABLE IF NOT EXISTS art_delegations (
    id          TEXT PRIMARY KEY,
    agent_id    TEXT NOT NULL,
    from_org    TEXT NOT NULL,
    to_org      TEXT NOT NULL,
    to_task_id  INTEGER,
    budget_usd  REAL NOT NULL DEFAULT 0.0,
    timeout_s   INTEGER NOT NULL DEFAULT 3600,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL,
    returned    INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (agent_id) REFERENCES art_agents(id)
);
CREATE INDEX IF NOT EXISTS idx_art_deleg_agent ON art_delegations(agent_id);
CREATE INDEX IF NOT EXISTS idx_art_deleg_expires ON art_delegations(expires_at);

CREATE TABLE IF NOT EXISTS art_queue (
    id          TEXT PRIMARY KEY,
    org_id      TEXT NOT NULL,
    agent_name  TEXT NOT NULL,
    task_id     INTEGER,
    capabilities TEXT NOT NULL DEFAULT '[]',
    model_pref  TEXT,
    budget_usd  REAL NOT NULL DEFAULT 0.0,
    priority    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_art_queue_priority
    ON art_queue(priority DESC, created_at ASC);",
        },
        Migration {
            version: 3,
            description: "scope enforcement rules",
            up: "\
CREATE TABLE IF NOT EXISTS art_scope_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id    TEXT NOT NULL,
    resource    TEXT NOT NULL,
    access      TEXT NOT NULL DEFAULT 'read',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (agent_id) REFERENCES art_agents(id),
    UNIQUE(agent_id, resource, access)
);
CREATE INDEX IF NOT EXISTS idx_art_scope_agent ON art_scope_rules(agent_id);",
        },
        Migration {
            version: 4,
            description: "per-agent live context",
            up: "\
CREATE TABLE IF NOT EXISTS art_context (
    agent_id    TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    set_by      TEXT NOT NULL DEFAULT 'system',
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, key),
    FOREIGN KEY (agent_id) REFERENCES art_agents(id)
);
CREATE INDEX IF NOT EXISTS idx_art_context_agent ON art_context(agent_id);",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_have_sequential_versions() {
        let migs = migrations();
        assert_eq!(migs.len(), 4);
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
                 AND name LIKE 'art_%'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 6);
    }
}
