//! DB migrations for multi-tenancy isolation tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "isolation policies and peer whitelist",
            up: "
                CREATE TABLE IF NOT EXISTS mt_isolation_policies (
                    org_id                   TEXT PRIMARY KEY,
                    db_prefix_enabled        INTEGER NOT NULL DEFAULT 1,
                    network_whitelist_enabled INTEGER NOT NULL DEFAULT 1,
                    secret_scope_enabled      INTEGER NOT NULL DEFAULT 1,
                    audit_isolation_enabled   INTEGER NOT NULL DEFAULT 1,
                    resource_limits_enabled   INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS mt_peer_whitelist (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id     TEXT    NOT NULL,
                    peer_name  TEXT    NOT NULL,
                    peer_url   TEXT    NOT NULL DEFAULT '',
                    allowed    INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                    UNIQUE (org_id, peer_name)
                );
                CREATE INDEX IF NOT EXISTS idx_mt_peer_wl_org
                    ON mt_peer_whitelist(org_id);
            ",
        },
        Migration {
            version: 2,
            description: "scoped secrets, resource limits, and usage tracking",
            up: "
                CREATE TABLE IF NOT EXISTS mt_scoped_secrets (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id          TEXT NOT NULL,
                    key             TEXT NOT NULL,
                    encrypted_value TEXT NOT NULL DEFAULT '',
                    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
                    UNIQUE (org_id, key)
                );
                CREATE INDEX IF NOT EXISTS idx_mt_secrets_org
                    ON mt_scoped_secrets(org_id);

                CREATE TABLE IF NOT EXISTS mt_resource_limits (
                    org_id                    TEXT PRIMARY KEY,
                    max_cpu_seconds_per_hour  INTEGER NOT NULL DEFAULT 3600,
                    max_memory_mb             INTEGER NOT NULL DEFAULT 4096,
                    max_storage_mb            INTEGER NOT NULL DEFAULT 10240,
                    max_concurrent_agents     INTEGER NOT NULL DEFAULT 20,
                    max_api_calls_per_minute  INTEGER NOT NULL DEFAULT 600
                );

                CREATE TABLE IF NOT EXISTS mt_resource_usage (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id                  TEXT    NOT NULL,
                    cpu_seconds_this_hour   REAL    NOT NULL DEFAULT 0.0,
                    memory_mb_current       REAL    NOT NULL DEFAULT 0.0,
                    storage_mb_current      REAL    NOT NULL DEFAULT 0.0,
                    active_agents           INTEGER NOT NULL DEFAULT 0,
                    api_calls_this_minute   INTEGER NOT NULL DEFAULT 0,
                    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_mt_usage_org
                    ON mt_resource_usage(org_id, recorded_at);
            ",
        },
        Migration {
            version: 3,
            description: "org audit trail and isolation violations",
            up: "
                CREATE TABLE IF NOT EXISTS mt_org_audit (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id     TEXT NOT NULL,
                    agent_id   TEXT NOT NULL DEFAULT '',
                    action     TEXT NOT NULL,
                    target     TEXT NOT NULL DEFAULT '',
                    details    TEXT NOT NULL DEFAULT '',
                    prev_hash  TEXT NOT NULL DEFAULT '',
                    entry_hash TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_mt_audit_org
                    ON mt_org_audit(org_id, created_at);

                CREATE TABLE IF NOT EXISTS mt_isolation_violations (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id         TEXT    NOT NULL,
                    violation_type TEXT    NOT NULL,
                    details        TEXT    NOT NULL DEFAULT '',
                    blocked        INTEGER NOT NULL DEFAULT 1,
                    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_mt_violations_org
                    ON mt_isolation_violations(org_id, created_at);
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
        let applied =
            convergio_db::migration::apply_migrations(&conn, "multitenancy", &migrations())
                .unwrap();
        assert_eq!(applied, 3);
    }
}
