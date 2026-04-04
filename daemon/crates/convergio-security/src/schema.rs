//! DB migrations for security tables (trust, secrets, sandbox).

use convergio_types::extension::Migration;

/// Raw SQL for all tables — used by in-memory test helpers.
pub const ALL_TABLES: &str = "
    CREATE TABLE IF NOT EXISTS peer_trust (
        peer_name   TEXT PRIMARY KEY,
        trust_level INTEGER NOT NULL DEFAULT 0,
        granted_by  TEXT NOT NULL,
        reason      TEXT NOT NULL DEFAULT '',
        granted_at  TEXT NOT NULL DEFAULT (datetime('now')),
        expires_at  TEXT
    );

    CREATE TABLE IF NOT EXISTS secret_filters (
        env_var         TEXT PRIMARY KEY,
        min_trust_level INTEGER NOT NULL DEFAULT 2,
        description     TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS sandbox_overrides (
        peer_name        TEXT PRIMARY KEY,
        allow_network    INTEGER NOT NULL DEFAULT 0,
        allow_disk_write INTEGER NOT NULL DEFAULT 0,
        max_cpu_seconds  INTEGER NOT NULL DEFAULT 60,
        max_memory_mb    INTEGER NOT NULL DEFAULT 512,
        allowed_commands TEXT NOT NULL DEFAULT '[]',
        blocked_paths    TEXT NOT NULL DEFAULT '[]'
    );
";

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "peer trust, secret filters, sandbox overrides",
        up: ALL_TABLES,
    }]
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
            convergio_db::migration::apply_migrations(&conn, "security", &migrations()).unwrap();
        assert_eq!(applied, 1);
    }
}
