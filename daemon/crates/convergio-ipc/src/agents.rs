use rusqlite::params;

use crate::types::{AgentInfo, IpcError, IpcResult};
use convergio_db::pool::ConnPool;

pub fn register(
    pool: &ConnPool,
    name: &str,
    agent_type: &str,
    pid: Option<u32>,
    host: &str,
    metadata: Option<&str>,
    parent_agent: Option<&str>,
) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute(
        "INSERT INTO ipc_agents (name, host, agent_type, pid, metadata, parent_agent,
            registered_at, last_seen)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6,
            strftime('%Y-%m-%dT%H:%M:%f','now'), strftime('%Y-%m-%dT%H:%M:%f','now'))
         ON CONFLICT(name, host) DO UPDATE SET
           agent_type = excluded.agent_type, pid = excluded.pid,
           metadata = excluded.metadata, parent_agent = excluded.parent_agent,
           last_seen = strftime('%Y-%m-%dT%H:%M:%f','now')",
        params![name, host, agent_type, pid, metadata, parent_agent],
    )?;
    tracing::info!(agent = name, host, "agent registered");
    Ok(())
}

pub fn unregister(pool: &ConnPool, name: &str, host: &str) -> IpcResult<()> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_agents WHERE name = ?1 AND host = ?2",
        params![name, host],
    )?;
    if deleted == 0 {
        return Err(IpcError::NotFound(format!("{name}@{host}")));
    }
    tracing::info!(agent = name, host, "agent unregistered");
    Ok(())
}

pub fn list(pool: &ConnPool) -> IpcResult<Vec<AgentInfo>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT name, host, agent_type, pid, last_seen, parent_agent
         FROM ipc_agents ORDER BY name, host",
    )?;
    let agents = stmt
        .query_map([], |row| {
            Ok(AgentInfo {
                name: row.get(0)?,
                host: row.get(1)?,
                agent_type: row.get(2)?,
                pid: row.get(3)?,
                last_seen: row.get(4)?,
                parent_agent: row.get(5)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(agents)
}

pub fn heartbeat(pool: &ConnPool, name: &str, host: &str) -> IpcResult<()> {
    let conn = pool.get()?;
    let updated = conn.execute(
        "UPDATE ipc_agents SET last_seen = strftime('%Y-%m-%dT%H:%M:%f','now')
         WHERE name = ?1 AND host = ?2",
        params![name, host],
    )?;
    if updated == 0 {
        return Err(IpcError::NotFound(format!("{name}@{host}")));
    }
    Ok(())
}

pub fn prune_stale(pool: &ConnPool, ttl_secs: u64) -> IpcResult<usize> {
    let conn = pool.get()?;
    let pruned = conn.execute(
        "DELETE FROM ipc_agents WHERE last_seen < strftime('%Y-%m-%dT%H:%M:%f',
         'now', printf('-%d seconds', ?1))",
        params![ttl_secs],
    )?;
    if pruned > 0 {
        tracing::info!(count = pruned, "pruned stale agents");
    }
    Ok(pruned)
}

pub fn prune_dead_pids(pool: &ConnPool, local_host: &str) -> IpcResult<usize> {
    let conn = pool.get()?;
    let mut stmt =
        conn.prepare("SELECT name, host, pid FROM ipc_agents WHERE pid IS NOT NULL")?;
    let agents: Vec<(String, String, u32)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)))?
        .filter_map(|r| r.ok())
        .collect();

    let mut pruned = 0usize;
    for (name, host, pid) in &agents {
        if host != local_host {
            continue;
        }
        if !is_pid_alive(*pid) {
            conn.execute(
                "DELETE FROM ipc_agents WHERE name = ?1 AND host = ?2",
                params![name, host],
            )?;
            pruned += 1;
        }
    }
    if pruned > 0 {
        tracing::info!(count = pruned, "pruned dead-PID agents");
    }
    Ok(pruned)
}

fn is_pid_alive(pid: u32) -> bool {
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
    fn register_and_list() {
        let p = pool();
        register(&p, "elena", "claude", Some(42), "m5max", None, None).unwrap();
        let agents = list(&p).unwrap();
        assert_eq!(agents.len(), 1);
        assert_eq!(agents[0].name, "elena");
    }

    #[test]
    fn unregister_not_found() {
        let p = pool();
        let err = unregister(&p, "ghost", "nowhere");
        assert!(matches!(err, Err(IpcError::NotFound(_))));
    }

    #[test]
    fn heartbeat_updates_last_seen() {
        let p = pool();
        register(&p, "baccio", "claude", None, "m1pro", None, None).unwrap();
        heartbeat(&p, "baccio", "m1pro").unwrap();
        let agents = list(&p).unwrap();
        assert_eq!(agents.len(), 1);
    }

    #[test]
    fn prune_stale_removes_old() {
        let p = pool();
        register(&p, "old", "claude", None, "h1", None, None).unwrap();
        {
            let conn = p.get().unwrap();
            conn.execute(
                "UPDATE ipc_agents SET last_seen = '2020-01-01T00:00:00.000'
                 WHERE name = 'old'",
                [],
            )
            .unwrap();
        }
        let pruned = prune_stale(&p, 60).unwrap();
        assert_eq!(pruned, 1);
    }
}
