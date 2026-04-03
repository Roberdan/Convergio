// Agent reaper — GC for stale agents, dead delegations, orphan tasks.
// Runs as periodic background task alongside Ali.

use convergio_db::pool::ConnPool;

const STALE_AGENT_MINUTES: i64 = 60;
const STALE_DELEGATION_HOURS: i64 = 24;

/// Reap stale agents, dead delegations, orphan messages.
pub fn reap(pool: &ConnPool) -> Result<(usize, usize, usize), Box<dyn std::error::Error>> {
    let conn = pool.get()?;

    // 1. Stale agents: no heartbeat in 60 min
    let agents_reaped = conn.execute(
        "DELETE FROM ipc_agents WHERE last_seen < datetime('now', ?1)",
        rusqlite::params![format!("-{STALE_AGENT_MINUTES} minutes")],
    )?;

    // 2. Dead delegations: plans assigned to peers but no progress in 24h
    let delegations_cleaned = conn.execute(
        "UPDATE plans SET execution_host=NULL \
         WHERE execution_host IS NOT NULL \
         AND status='doing' \
         AND updated_at < datetime('now', ?1)",
        rusqlite::params![format!("-{STALE_DELEGATION_HOURS} hours")],
    )?;

    // 3. Orphan IPC messages: older than 7 days
    let sessions_cleaned = conn
        .execute(
            "DELETE FROM ipc_messages WHERE created_at < datetime('now', '-7 days')",
            [],
        )
        .unwrap_or(0);

    // 4. Orphan tasks: in_progress but assigned agent is dead
    let orphan_tasks = conn
        .execute(
            "UPDATE tasks SET status='pending', executor_agent=NULL \
         WHERE status='in_progress' \
         AND executor_agent IS NOT NULL \
         AND executor_agent NOT IN (SELECT name FROM ipc_agents)",
            [],
        )
        .unwrap_or(0);
    if orphan_tasks > 0 {
        tracing::warn!("reaper: reset {orphan_tasks} orphan in_progress tasks to pending");
    }

    // 5. Expired file locks
    if let Err(e) = conn.execute(
        "DELETE FROM ipc_file_locks WHERE expires_at IS NOT NULL AND expires_at < datetime('now')",
        [],
    ) {
        tracing::warn!("reaper: expired lock cleanup: {e}");
    }

    if agents_reaped > 0 || delegations_cleaned > 0 || sessions_cleaned > 0 {
        tracing::info!(
            "reaper: reaped {agents_reaped} agents, {delegations_cleaned} delegations, {sessions_cleaned} messages"
        );
    }

    Ok((agents_reaped, delegations_cleaned, sessions_cleaned))
}

/// Kill orphaned copilot/claude processes older than `max_age`.
pub fn reap_orphan_processes(max_age: std::time::Duration) -> usize {
    let output = std::process::Command::new("ps")
        .args(["-eo", "pid,etime,command"])
        .output();
    let max_secs = max_age.as_secs();
    let mut killed = 0usize;
    if let Ok(out) = output {
        let stdout = String::from_utf8_lossy(&out.stdout);
        for line in stdout.lines() {
            if !line.contains("copilot") || !line.contains("yolo") {
                continue;
            }
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 3 {
                continue;
            }
            let pid: i32 = match parts[0].parse() {
                Ok(p) => p,
                Err(_) => continue,
            };
            let age = parse_etime(parts[1]);
            if age >= max_secs {
                unsafe {
                    libc::kill(pid, libc::SIGTERM);
                }
                killed += 1;
                tracing::info!("reaper: killed orphan copilot pid={pid} age={age}s");
            }
        }
    }
    killed
}

/// Parse ps etime format [[dd-]hh:]mm:ss into seconds.
fn parse_etime(s: &str) -> u64 {
    let (days, rest) = if let Some(i) = s.find('-') {
        (s[..i].parse::<u64>().unwrap_or(0), &s[i + 1..])
    } else {
        (0, s)
    };
    let parts: Vec<u64> = rest.split(':').filter_map(|p| p.parse().ok()).collect();
    let (h, m, sec) = match parts.len() {
        3 => (parts[0], parts[1], parts[2]),
        2 => (0, parts[0], parts[1]),
        1 => (0, 0, parts[0]),
        _ => return 0,
    };
    days * 86400 + h * 3600 + m * 60 + sec
}

/// Spawn the reaper as a periodic background task (every 5 min).
pub fn spawn_reaper(pool: ConnPool) {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(300));
        loop {
            interval.tick().await;
            match reap(&pool) {
                Ok((a, d, s)) => {
                    if a + d + s > 0 {
                        tracing::info!("reaper cycle: agents={a} delegations={d} messages={s}");
                    }
                }
                Err(e) => tracing::warn!("reaper error: {e}"),
            }
            let killed = reap_orphan_processes(std::time::Duration::from_secs(7200));
            if killed > 0 {
                tracing::info!("reaper: killed {killed} orphan copilot processes");
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> ConnPool {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        // Disable FK enforcement in tests to allow inserting without full referential chain
        conn.execute_batch("PRAGMA foreign_keys = OFF;").unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "ipc",
            &convergio_ipc::schema::migrations(),
        )
        .unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "orchestrator",
            &crate::schema::migrations(),
        )
        .unwrap();
        pool
    }

    #[test]
    fn reap_removes_stale_agents() {
        let pool = setup();
        {
            let conn = pool.get().unwrap();
            conn.execute_batch("PRAGMA foreign_keys = OFF;").unwrap();
            conn.execute("INSERT INTO ipc_agents(name, host, agent_type, last_seen) VALUES ('stale', 'h', 't', datetime('now', '-2 hours'))", []).unwrap();
            conn.execute("INSERT INTO ipc_agents(name, host, agent_type, last_seen) VALUES ('fresh', 'h', 't', datetime('now'))", []).unwrap();
        } // drop conn before reap
        let (reaped, _, _) = reap(&pool).unwrap();
        assert!(reaped >= 1);
        let conn = pool.get().unwrap();
        let c: i64 = conn
            .query_row("SELECT COUNT(*) FROM ipc_agents", [], |r| r.get(0))
            .unwrap();
        assert_eq!(c, 1);
    }

    #[test]
    fn reap_resets_orphan_tasks() {
        let pool = setup();
        {
            let conn = pool.get().unwrap();
            conn.execute_batch("PRAGMA foreign_keys = OFF;").unwrap();
            conn.execute(
                "INSERT INTO plans(id, project_id, name) VALUES (100, 'p1', 'test')",
                [],
            )
            .unwrap();
            conn.execute("INSERT INTO tasks(id, plan_id, status, executor_agent) VALUES (1, 100, 'in_progress', 'dead-agent')", []).unwrap();
        } // drop conn before reap
        reap(&pool).unwrap();
        let conn = pool.get().unwrap();
        let s: String = conn
            .query_row("SELECT status FROM tasks WHERE id=1", [], |r| r.get(0))
            .unwrap();
        assert_eq!(s, "pending");
    }

    #[test]
    fn parse_etime_formats() {
        assert_eq!(parse_etime("05:30"), 330);
        assert_eq!(parse_etime("1:05:30"), 3930);
        assert_eq!(parse_etime("2-01:05:30"), 2 * 86400 + 3930);
    }

    #[test]
    fn reap_orphan_processes_does_not_panic() {
        assert_eq!(
            reap_orphan_processes(std::time::Duration::from_secs(999_999)),
            0
        );
    }
}
