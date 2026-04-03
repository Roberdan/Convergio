//! Database migrations for the agent catalog.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "agent catalog table",
        up: "
CREATE TABLE IF NOT EXISTS agent_catalog (
    id                TEXT PRIMARY KEY NOT NULL,
    name              TEXT NOT NULL UNIQUE,
    role              TEXT NOT NULL,
    org_id            TEXT NOT NULL DEFAULT 'convergio',
    category          TEXT NOT NULL,
    model_tier        TEXT NOT NULL DEFAULT 't2',
    max_tokens        INTEGER NOT NULL DEFAULT 200000,
    hourly_budget     REAL NOT NULL DEFAULT 0.0,
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    prompt_ref        TEXT,
    escalation_target TEXT,
    status            TEXT NOT NULL DEFAULT 'active',
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_cat ON agent_catalog(category);
CREATE INDEX IF NOT EXISTS idx_agent_status ON agent_catalog(status);
CREATE INDEX IF NOT EXISTS idx_agent_org ON agent_catalog(org_id);
",
    }]
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    #[test]
    fn migrations_apply_cleanly() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        let n = convergio_db::migration::apply_migrations(&conn, "agents", &migrations()).unwrap();
        assert_eq!(n, 1);
    }

    #[test]
    fn migrations_are_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "agents", &migrations()).unwrap();
        let n = convergio_db::migration::apply_migrations(&conn, "agents", &migrations()).unwrap();
        assert_eq!(n, 0);
    }
}
