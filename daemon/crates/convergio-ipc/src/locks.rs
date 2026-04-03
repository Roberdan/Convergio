use rusqlite::{params, OptionalExtension};

use crate::types::{AcquireResult, FileLock, IpcResult};
use convergio_db::pool::ConnPool;

pub fn acquire(
    pool: &ConnPool,
    file_path: &str,
    agent: &str,
    host: &str,
    pid: i64,
) -> IpcResult<AcquireResult> {
    let conn = pool.get()?;
    let tx = conn.unchecked_transaction()?;

    let existing: Option<FileLock> = tx
        .query_row(
            "SELECT file_path, locked_by, host, pid, locked_at
             FROM ipc_file_locks WHERE file_path = ?1",
            params![file_path],
            map_lock,
        )
        .optional()?;

    if let Some(lock) = existing {
        if lock.locked_by == agent && lock.host == host {
            tx.execute(
                "UPDATE ipc_file_locks SET pid = ?1, locked_at = strftime('%Y-%m-%dT%H:%M:%f','now')
                 WHERE file_path = ?2",
                params![pid, file_path],
            )?;
            tx.commit()?;
            return Ok(AcquireResult::Acquired);
        }
        tx.commit()?;
        return Ok(AcquireResult::Rejected(lock));
    }

    tx.execute(
        "INSERT INTO ipc_file_locks (file_path, locked_by, host, pid)
         VALUES (?1, ?2, ?3, ?4)",
        params![file_path, agent, host, pid],
    )?;
    tx.commit()?;
    Ok(AcquireResult::Acquired)
}

pub fn release(pool: &ConnPool, file_path: &str, agent: &str, host: &str) -> IpcResult<bool> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_file_locks WHERE file_path = ?1 AND locked_by = ?2 AND host = ?3",
        params![file_path, agent, host],
    )?;
    Ok(deleted > 0)
}

pub fn list_locks(pool: &ConnPool) -> IpcResult<Vec<FileLock>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT file_path, locked_by, host, pid, locked_at
         FROM ipc_file_locks ORDER BY locked_at DESC",
    )?;
    let locks = stmt.query_map([], map_lock)?.filter_map(|r| r.ok()).collect();
    Ok(locks)
}

pub fn prune_dead(pool: &ConnPool, local_host: &str) -> IpcResult<usize> {
    let locks = list_locks(pool)?;
    let conn = pool.get()?;
    let mut pruned = 0;
    for lock in &locks {
        if lock.host != local_host {
            continue;
        }
        if !is_pid_alive(lock.pid) {
            conn.execute(
                "DELETE FROM ipc_file_locks WHERE file_path = ?1 AND locked_by = ?2 AND host = ?3",
                params![lock.file_path, lock.locked_by, lock.host],
            )?;
            pruned += 1;
        }
    }
    Ok(pruned)
}

fn is_pid_alive(pid: i64) -> bool {
    #[cfg(unix)]
    {
        unsafe { libc::kill(pid as i32, 0) == 0 }
    }
    #[cfg(not(unix))]
    {
        let _ = pid;
        true
    }
}

fn map_lock(row: &rusqlite::Row<'_>) -> rusqlite::Result<FileLock> {
    Ok(FileLock {
        file_path: row.get(0)?,
        locked_by: row.get(1)?,
        host: row.get(2)?,
        pid: row.get(3)?,
        locked_at: row.get(4)?,
    })
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
    fn acquire_and_release() {
        let p = pool();
        let r = acquire(&p, "src/main.rs", "elena", "m5max", 1234).unwrap();
        assert_eq!(r, AcquireResult::Acquired);
        let locks = list_locks(&p).unwrap();
        assert_eq!(locks.len(), 1);
        assert!(release(&p, "src/main.rs", "elena", "m5max").unwrap());
        assert_eq!(list_locks(&p).unwrap().len(), 0);
    }

    #[test]
    fn reacquire_by_same_agent() {
        let p = pool();
        acquire(&p, "f.rs", "elena", "m5max", 100).unwrap();
        let r = acquire(&p, "f.rs", "elena", "m5max", 200).unwrap();
        assert_eq!(r, AcquireResult::Acquired);
    }

    #[test]
    fn rejected_by_different_agent() {
        let p = pool();
        acquire(&p, "f.rs", "elena", "m5max", 100).unwrap();
        let r = acquire(&p, "f.rs", "baccio", "m1pro", 200).unwrap();
        assert!(matches!(r, AcquireResult::Rejected(_)));
    }
}
