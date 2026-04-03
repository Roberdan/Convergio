use rusqlite::params;

use crate::types::{ChannelInfo, ContextEntry, IpcError, IpcResult};
use convergio_db::pool::ConnPool;

// ── Channels ─────────────────────────────────────

pub fn create_channel(
    pool: &ConnPool,
    name: &str,
    description: Option<&str>,
    created_by: &str,
) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute(
        "INSERT OR IGNORE INTO ipc_channels (name, description, created_by)
         VALUES (?1, ?2, ?3)",
        params![name, description, created_by],
    )?;
    Ok(())
}

pub fn list_channels(pool: &ConnPool) -> IpcResult<Vec<ChannelInfo>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT name, description, created_by, created_at
         FROM ipc_channels ORDER BY name",
    )?;
    let channels = stmt
        .query_map([], |row| {
            Ok(ChannelInfo {
                name: row.get(0)?,
                description: row.get(1)?,
                created_by: row.get(2)?,
                created_at: row.get(3)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(channels)
}

// ── Shared Context (LWW register) ────────────────

pub fn context_get(pool: &ConnPool, key: &str) -> IpcResult<ContextEntry> {
    let conn = pool.get()?;
    conn.query_row(
        "SELECT key, value, version, set_by, updated_at
         FROM ipc_shared_context WHERE key = ?1",
        params![key],
        |row| {
            Ok(ContextEntry {
                key: row.get(0)?,
                value: row.get(1)?,
                version: row.get(2)?,
                set_by: row.get(3)?,
                updated_at: row.get(4)?,
            })
        },
    )
    .map_err(|e| match e {
        rusqlite::Error::QueryReturnedNoRows => IpcError::NotFound(format!("key '{key}'")),
        other => IpcError::Db(other),
    })
}

pub fn context_set(pool: &ConnPool, key: &str, value: &str, set_by: &str) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute(
        "INSERT INTO ipc_shared_context (key, value, version, set_by, updated_at)
         VALUES (?1, ?2, 1, ?3, strftime('%Y-%m-%dT%H:%M:%f','now'))
         ON CONFLICT(key) DO UPDATE SET
           value = excluded.value,
           version = ipc_shared_context.version + 1,
           set_by = excluded.set_by,
           updated_at = strftime('%Y-%m-%dT%H:%M:%f','now')",
        params![key, value, set_by],
    )?;
    Ok(())
}

pub fn context_list(pool: &ConnPool) -> IpcResult<Vec<ContextEntry>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT key, value, version, set_by, updated_at
         FROM ipc_shared_context ORDER BY key",
    )?;
    let entries = stmt
        .query_map([], |row| {
            Ok(ContextEntry {
                key: row.get(0)?,
                value: row.get(1)?,
                version: row.get(2)?,
                set_by: row.get(3)?,
                updated_at: row.get(4)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(entries)
}

pub fn context_delete(pool: &ConnPool, key: &str) -> IpcResult<()> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_shared_context WHERE key = ?1",
        params![key],
    )?;
    if deleted == 0 {
        return Err(IpcError::NotFound(format!("key '{key}'")));
    }
    Ok(())
}

// ── DB Maintenance ───────────────────────────────

pub fn cleanup_old_messages(pool: &ConnPool, older_than_days: u32) -> IpcResult<usize> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_messages
         WHERE created_at < datetime('now', '-' || ?1 || ' days')",
        params![older_than_days],
    )?;
    Ok(deleted)
}

pub fn vacuum(pool: &ConnPool) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE); VACUUM;")?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pool() -> ConnPool {
        let p = convergio_db::pool::create_memory_pool().unwrap();
        let conn = p.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &crate::schema::migrations())
            .unwrap();
        p
    }

    #[test]
    fn channel_crud() {
        let p = pool();
        create_channel(&p, "general", Some("Main channel"), "admin").unwrap();
        let channels = list_channels(&p).unwrap();
        assert_eq!(channels.len(), 1);
        assert_eq!(channels[0].name, "general");
    }

    #[test]
    fn context_set_get_delete() {
        let p = pool();
        context_set(&p, "plan_id", "42", "elena").unwrap();
        let entry = context_get(&p, "plan_id").unwrap();
        assert_eq!(entry.value, "42");
        assert_eq!(entry.version, 1);

        context_set(&p, "plan_id", "43", "baccio").unwrap();
        let entry = context_get(&p, "plan_id").unwrap();
        assert_eq!(entry.value, "43");
        assert_eq!(entry.version, 2);

        context_delete(&p, "plan_id").unwrap();
        assert!(matches!(
            context_get(&p, "plan_id"),
            Err(IpcError::NotFound(_))
        ));
    }

    #[test]
    fn context_list_returns_all() {
        let p = pool();
        context_set(&p, "a", "1", "x").unwrap();
        context_set(&p, "b", "2", "x").unwrap();
        let entries = context_list(&p).unwrap();
        assert_eq!(entries.len(), 2);
    }
}
