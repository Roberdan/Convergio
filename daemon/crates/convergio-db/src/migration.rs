//! Migration runner — collects migrations from extensions, applies in order.
//!
//! Each extension declares its migrations via Extension::migrations().
//! The runner tracks applied versions in `_schema_registry`.

use convergio_types::extension::Migration;
use rusqlite::Connection;

/// Ensures the schema registry table exists.
pub fn ensure_registry(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS _schema_registry (
            module TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )",
    )
}

/// Returns the current version for a module, or 0 if not yet applied.
pub fn current_version(conn: &Connection, module: &str) -> rusqlite::Result<u32> {
    let mut stmt = conn.prepare(
        "SELECT version FROM _schema_registry WHERE module = ?1",
    )?;
    let version = stmt
        .query_row([module], |row| row.get::<_, u32>(0))
        .unwrap_or(0);
    Ok(version)
}

/// Apply pending migrations for a module.
/// Migrations must be sorted by version (ascending).
/// Returns the number of migrations applied.
pub fn apply_migrations(
    conn: &Connection,
    module: &str,
    migrations: &[Migration],
) -> rusqlite::Result<usize> {
    ensure_registry(conn)?;
    let current = current_version(conn, module)?;
    let mut applied = 0;

    for m in migrations {
        if m.version <= current {
            continue;
        }
        tracing::info!(
            module,
            version = m.version,
            desc = m.description,
            "applying migration"
        );
        conn.execute_batch(m.up)?;
        conn.execute(
            "INSERT OR REPLACE INTO _schema_registry (module, version) VALUES (?1, ?2)",
            rusqlite::params![module, m.version],
        )?;
        applied += 1;
    }
    Ok(applied)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_conn() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        conn
    }

    #[test]
    fn registry_created_on_first_run() {
        let conn = test_conn();
        ensure_registry(&conn).unwrap();
        let exists: bool = conn
            .query_row(
                "SELECT COUNT(*) > 0 FROM sqlite_master WHERE name = '_schema_registry'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert!(exists);
    }

    #[test]
    fn applies_migrations_in_order() {
        let conn = test_conn();
        let migrations = vec![
            Migration {
                version: 1,
                description: "create users",
                up: "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)",
            },
            Migration {
                version: 2,
                description: "add email",
                up: "ALTER TABLE users ADD COLUMN email TEXT",
            },
        ];
        let applied = apply_migrations(&conn, "test-mod", &migrations).unwrap();
        assert_eq!(applied, 2);
        assert_eq!(current_version(&conn, "test-mod").unwrap(), 2);
    }

    #[test]
    fn skips_already_applied() {
        let conn = test_conn();
        let migrations = vec![Migration {
            version: 1,
            description: "create table",
            up: "CREATE TABLE t1 (id INTEGER PRIMARY KEY)",
        }];
        apply_migrations(&conn, "mod-a", &migrations).unwrap();
        let applied = apply_migrations(&conn, "mod-a", &migrations).unwrap();
        assert_eq!(applied, 0);
    }
}
