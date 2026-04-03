use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "core IPC tables",
            up: "
CREATE TABLE IF NOT EXISTS ipc_agents (
    name        TEXT NOT NULL,
    host        TEXT NOT NULL,
    agent_type  TEXT NOT NULL DEFAULT 'claude',
    pid         INTEGER,
    metadata    TEXT,
    parent_agent TEXT,
    registered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    last_seen   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    PRIMARY KEY (name, host)
);

CREATE TABLE IF NOT EXISTS ipc_messages (
    id          TEXT PRIMARY KEY NOT NULL,
    from_agent  TEXT NOT NULL DEFAULT '',
    to_agent    TEXT,
    channel     TEXT,
    content     TEXT NOT NULL DEFAULT '',
    msg_type    TEXT NOT NULL DEFAULT 'text',
    priority    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    read_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_ipc_messages_to ON ipc_messages(to_agent);
CREATE INDEX IF NOT EXISTS idx_ipc_messages_channel ON ipc_messages(channel, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ipc_messages_created ON ipc_messages(created_at);

CREATE TABLE IF NOT EXISTS ipc_channels (
    name        TEXT PRIMARY KEY NOT NULL,
    description TEXT,
    created_by  TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);

CREATE TABLE IF NOT EXISTS ipc_shared_context (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    set_by      TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);

CREATE TABLE IF NOT EXISTS ipc_file_locks (
    file_path   TEXT NOT NULL,
    locked_by   TEXT NOT NULL DEFAULT '',
    host        TEXT NOT NULL DEFAULT '',
    pid         INTEGER NOT NULL DEFAULT 0,
    locked_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    PRIMARY KEY (file_path)
);

CREATE TABLE IF NOT EXISTS ipc_agent_skills (
    id          INTEGER PRIMARY KEY,
    agent       TEXT NOT NULL,
    host        TEXT NOT NULL,
    skill       TEXT NOT NULL,
    confidence  REAL NOT NULL DEFAULT 0.5,
    last_used   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    UNIQUE(agent, host, skill)
);
",
        },
        Migration {
            version: 2,
            description: "model registry and budget tables",
            up: "
CREATE TABLE IF NOT EXISTS ipc_model_registry (
    id          INTEGER PRIMARY KEY,
    host        TEXT NOT NULL,
    provider    TEXT NOT NULL,
    model       TEXT NOT NULL,
    size_gb     REAL NOT NULL DEFAULT 0.0,
    quantization TEXT NOT NULL DEFAULT '',
    last_seen   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    UNIQUE(host, provider, model)
);

CREATE TABLE IF NOT EXISTS ipc_node_capabilities (
    host        TEXT NOT NULL,
    provider    TEXT NOT NULL,
    models      TEXT NOT NULL DEFAULT '[]',
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    PRIMARY KEY (host, provider)
);

CREATE TABLE IF NOT EXISTS ipc_subscriptions (
    name        TEXT PRIMARY KEY,
    provider    TEXT NOT NULL,
    plan        TEXT NOT NULL,
    budget_usd  REAL NOT NULL DEFAULT 0.0,
    reset_day   INTEGER NOT NULL DEFAULT 1,
    models      TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS ipc_budget_log (
    id              INTEGER PRIMARY KEY,
    subscription    TEXT NOT NULL,
    date            TEXT NOT NULL,
    tokens_in       INTEGER NOT NULL DEFAULT 0,
    tokens_out      INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd REAL NOT NULL DEFAULT 0.0,
    model           TEXT NOT NULL DEFAULT '',
    task_ref        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_budget_log_sub ON ipc_budget_log(subscription, date);
",
        },
        Migration {
            version: 3,
            description: "org tables and isolation triggers",
            up: "
CREATE TABLE IF NOT EXISTS ipc_orgs (
    id          TEXT PRIMARY KEY NOT NULL,
    mission     TEXT NOT NULL,
    objectives  TEXT NOT NULL,
    ceo_agent   TEXT NOT NULL,
    budget      REAL NOT NULL DEFAULT 0,
    daily_budget_tokens INTEGER NOT NULL DEFAULT 1000,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
);

CREATE TABLE IF NOT EXISTS ipc_org_members (
    id          TEXT PRIMARY KEY NOT NULL,
    org_id      TEXT NOT NULL REFERENCES ipc_orgs(id) ON DELETE CASCADE,
    agent       TEXT NOT NULL,
    role        TEXT NOT NULL,
    department  TEXT,
    joined_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    UNIQUE(org_id, agent)
);
CREATE INDEX IF NOT EXISTS idx_org_members ON ipc_org_members(org_id, agent);

CREATE TABLE IF NOT EXISTS ipc_service_requests (
    id              TEXT PRIMARY KEY NOT NULL,
    requester_org   TEXT NOT NULL REFERENCES ipc_orgs(id),
    provider_org    TEXT NOT NULL REFERENCES ipc_orgs(id),
    service_name    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    cost            REAL,
    request_payload TEXT,
    response_payload TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now')),
    completed_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_svc_req ON ipc_service_requests(requester_org, status);

CREATE TRIGGER IF NOT EXISTS trg_ipc_org_isolation
BEFORE INSERT ON ipc_messages
WHEN NEW.channel LIKE 'org:%'
  AND NEW.from_agent IS NOT NULL AND NEW.from_agent != ''
  AND NOT EXISTS (
      SELECT 1 FROM ipc_org_members m
      WHERE m.org_id = substr(NEW.channel, 5) AND m.agent = NEW.from_agent
  )
BEGIN
    SELECT RAISE(ABORT, 'org isolation violation');
END;
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
        let applied = convergio_db::migration::apply_migrations(&conn, "ipc", &migrations());
        assert_eq!(applied.unwrap(), 3);
    }

    #[test]
    fn migrations_are_idempotent() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &migrations()).unwrap();
        let applied = convergio_db::migration::apply_migrations(&conn, "ipc", &migrations());
        assert_eq!(applied.unwrap(), 0);
    }

    #[test]
    fn agent_pk_is_name_host() {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &migrations()).unwrap();
        conn.execute(
            "INSERT INTO ipc_agents (name, host) VALUES ('planner', 'mac1')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO ipc_agents (name, host) VALUES ('planner', 'linux1')",
            [],
        )
        .unwrap();
        let err = conn.execute(
            "INSERT INTO ipc_agents (name, host) VALUES ('planner', 'mac1')",
            [],
        );
        assert!(err.is_err());
    }
}
