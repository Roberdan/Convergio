//! Database migrations for prompt management and skill registry.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "prompt templates and skill registry",
            up: "
CREATE TABLE IF NOT EXISTS prompt_templates (
    id          TEXT PRIMARY KEY NOT NULL,
    name        TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    body        TEXT NOT NULL,
    variables   TEXT NOT NULL DEFAULT '[]',
    category    TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    UNIQUE(name, version)
);
CREATE INDEX IF NOT EXISTS idx_prompt_name ON prompt_templates(name, active);
CREATE INDEX IF NOT EXISTS idx_prompt_category ON prompt_templates(category);

CREATE TABLE IF NOT EXISTS prompt_skills (
    id              TEXT PRIMARY KEY NOT NULL,
    agent           TEXT NOT NULL,
    host            TEXT NOT NULL,
    capability      TEXT NOT NULL,
    confidence      REAL NOT NULL DEFAULT 0.5,
    description     TEXT NOT NULL DEFAULT '',
    last_used       TEXT,
    registered_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    UNIQUE(agent, host, capability)
);
CREATE INDEX IF NOT EXISTS idx_skill_cap ON prompt_skills(capability, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_skill_agent ON prompt_skills(agent);
",
        },
        Migration {
            version: 2,
            description: "A/B testing and token tracking",
            up: "
CREATE TABLE IF NOT EXISTS prompt_ab_tests (
    test_id     TEXT PRIMARY KEY NOT NULL,
    prompt_a_id TEXT NOT NULL REFERENCES prompt_templates(id),
    prompt_b_id TEXT NOT NULL REFERENCES prompt_templates(id),
    task_ref    TEXT NOT NULL,
    winner      TEXT,
    tokens_a    INTEGER NOT NULL DEFAULT 0,
    tokens_b    INTEGER NOT NULL DEFAULT 0,
    score_a     REAL NOT NULL DEFAULT 0.0,
    score_b     REAL NOT NULL DEFAULT 0.0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);
CREATE INDEX IF NOT EXISTS idx_ab_task ON prompt_ab_tests(task_ref);

CREATE TABLE IF NOT EXISTS prompt_token_usage (
    id          INTEGER PRIMARY KEY,
    prompt_id   TEXT NOT NULL REFERENCES prompt_templates(id),
    tokens      INTEGER NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);
CREATE INDEX IF NOT EXISTS idx_token_prompt ON prompt_token_usage(prompt_id);
",
        },
        Migration {
            version: 3,
            description: "spawned prompt snapshots for immutability",
            up: "
CREATE TABLE IF NOT EXISTS prompt_spawned (
    spawn_id            TEXT PRIMARY KEY NOT NULL,
    agent               TEXT NOT NULL,
    task_id             TEXT NOT NULL,
    rendered_body       TEXT NOT NULL,
    prompt_template_id  TEXT NOT NULL,
    prompt_version      INTEGER NOT NULL,
    spawned_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);
CREATE INDEX IF NOT EXISTS idx_spawned_agent ON prompt_spawned(agent, task_id);
CREATE INDEX IF NOT EXISTS idx_spawned_task ON prompt_spawned(task_id);
",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use rusqlite::Connection;

    #[test]
    fn migrations_apply_cleanly() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        let applied = convergio_db::migration::apply_migrations(&conn, "prompts", &migrations());
        assert_eq!(applied.unwrap(), 3);
    }

    #[test]
    fn migrations_are_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "prompts", &migrations()).unwrap();
        let applied = convergio_db::migration::apply_migrations(&conn, "prompts", &migrations());
        assert_eq!(applied.unwrap(), 0);
    }
}
