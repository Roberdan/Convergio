use std::sync::Arc;
use std::time::Duration;

use rusqlite::params;
use tokio::sync::Notify;

use crate::types::{IpcError, IpcResult, MessageInfo};
use convergio_db::pool::ConnPool;

pub const DEFAULT_RATE_LIMIT: u32 = 100;

pub fn send(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    from: &str,
    to: &str,
    content: &str,
    msg_type: &str,
    priority: i32,
    rate_limit: u32,
) -> IpcResult<String> {
    let conn = pool.get()?;
    check_rate_limit(&conn, from, rate_limit)?;
    let id = generate_msg_id();
    conn.execute(
        "INSERT INTO ipc_messages (id, from_agent, to_agent, content, msg_type, priority)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![id, from, to, content, msg_type, priority],
    )?;
    notify.notify_waiters();
    Ok(id)
}

pub fn broadcast(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    from: &str,
    content: &str,
    msg_type: &str,
    channel: Option<&str>,
    rate_limit: u32,
) -> IpcResult<String> {
    let conn = pool.get()?;
    check_rate_limit(&conn, from, rate_limit)?;
    let id = generate_msg_id();
    conn.execute(
        "INSERT INTO ipc_messages (id, from_agent, to_agent, channel, content, msg_type)
         VALUES (?1, ?2, NULL, ?3, ?4, ?5)",
        params![id, from, channel, content, msg_type],
    )?;
    notify.notify_waiters();
    Ok(id)
}

pub fn receive(
    pool: &ConnPool,
    agent: &str,
    from_filter: Option<&str>,
    channel_filter: Option<&str>,
    limit: u32,
    peek: bool,
) -> IpcResult<Vec<MessageInfo>> {
    let conn = pool.get()?;
    let tx = conn.unchecked_transaction()?;
    let mut conditions = vec!["(to_agent = ?1 OR to_agent IS NULL)".to_string()];
    let mut p: Vec<Box<dyn rusqlite::types::ToSql>> = vec![Box::new(agent.to_string())];
    if let Some(from) = from_filter {
        p.push(Box::new(from.to_string()));
        conditions.push(format!("from_agent = ?{}", p.len()));
    }
    if let Some(ch) = channel_filter {
        p.push(Box::new(ch.to_string()));
        conditions.push(format!("channel = ?{}", p.len()));
    }
    let sql = format!(
        "SELECT id, from_agent, to_agent, channel, content, msg_type, created_at
         FROM ipc_messages WHERE {} AND read_at IS NULL
         ORDER BY created_at ASC LIMIT {limit}",
        conditions.join(" AND ")
    );
    let refs: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|v| v.as_ref()).collect();
    let mut stmt = tx.prepare(&sql)?;
    let rows: Vec<(String, MessageInfo)> = stmt
        .query_map(refs.as_slice(), |row| {
            Ok((row.get::<_, String>(0)?, map_message(row)?))
        })?
        .filter_map(|r| r.ok())
        .collect();
    drop(stmt);

    if !peek {
        for (id, _) in &rows {
            tx.execute(
                "UPDATE ipc_messages SET read_at = strftime('%Y-%m-%dT%H:%M:%f','now')
                 WHERE id = ?1",
                params![id],
            )?;
        }
    }
    tx.commit()?;
    Ok(rows.into_iter().map(|(_, m)| m).collect())
}

pub async fn receive_wait(
    pool: &ConnPool,
    notify: &Arc<Notify>,
    agent: &str,
    from_filter: Option<&str>,
    channel_filter: Option<&str>,
    limit: u32,
    timeout_secs: u64,
) -> IpcResult<Vec<MessageInfo>> {
    let msgs = receive(pool, agent, from_filter, channel_filter, limit, false)?;
    if !msgs.is_empty() {
        return Ok(msgs);
    }
    let n = notify.clone();
    let a = agent.to_string();
    let f = from_filter.map(String::from);
    let c = channel_filter.map(String::from);
    match tokio::time::timeout(Duration::from_secs(timeout_secs), async {
        loop {
            n.notified().await;
            let msgs = receive(pool, &a, f.as_deref(), c.as_deref(), limit, false)?;
            if !msgs.is_empty() {
                return Ok(msgs);
            }
        }
    })
    .await
    {
        Ok(result) => result,
        Err(_) => Ok(Vec::new()),
    }
}

pub fn history(
    pool: &ConnPool,
    agent_filter: Option<&str>,
    channel_filter: Option<&str>,
    limit: u32,
    since: Option<&str>,
) -> IpcResult<Vec<MessageInfo>> {
    let conn = pool.get()?;
    let mut conds: Vec<String> = Vec::new();
    let mut p: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    if let Some(agent) = agent_filter {
        p.push(Box::new(agent.to_string()));
        let i = p.len();
        conds.push(format!("(from_agent = ?{i} OR to_agent = ?{i})"));
    }
    if let Some(ch) = channel_filter {
        p.push(Box::new(ch.to_string()));
        conds.push(format!("channel = ?{}", p.len()));
    }
    if let Some(ts) = since {
        p.push(Box::new(ts.to_string()));
        conds.push(format!("created_at >= ?{}", p.len()));
    }
    let where_cl = if conds.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conds.join(" AND "))
    };
    let sql = format!(
        "SELECT id, from_agent, to_agent, channel, content, msg_type, created_at
         FROM ipc_messages {where_cl} ORDER BY created_at DESC LIMIT {limit}"
    );
    let refs: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|v| v.as_ref()).collect();
    let mut stmt = conn.prepare(&sql)?;
    let msgs = stmt
        .query_map(refs.as_slice(), |row| map_message(row))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(msgs)
}

fn check_rate_limit(
    conn: &rusqlite::Connection,
    from: &str,
    limit: u32,
) -> IpcResult<()> {
    let count: u32 = conn.query_row(
        "SELECT COUNT(*) FROM ipc_messages
         WHERE from_agent = ?1 AND created_at > datetime('now', '-1 minute')",
        params![from],
        |r| r.get(0),
    )?;
    if count >= limit {
        return Err(IpcError::RateLimited(format!(
            "agent '{from}' exceeded {limit} msgs/min"
        )));
    }
    Ok(())
}

fn generate_msg_id() -> String {
    uuid::Uuid::new_v4().to_string()
}

fn map_message(row: &rusqlite::Row<'_>) -> rusqlite::Result<MessageInfo> {
    Ok(MessageInfo {
        id: row.get(0)?,
        from_agent: row.get(1)?,
        to_agent: row.get(2)?,
        channel: row.get(3)?,
        content: row.get(4)?,
        msg_type: row.get(5)?,
        created_at: row.get(6)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> (ConnPool, Arc<Notify>) {
        let p = convergio_db::pool::create_memory_pool().unwrap();
        let conn = p.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &crate::schema::migrations())
            .unwrap();
        (p, Arc::new(Notify::new()))
    }

    #[test]
    fn send_and_receive() {
        let (p, n) = setup();
        let id = send(&p, &n, "elena", "baccio", "ciao", "text", 0, 100).unwrap();
        assert!(!id.is_empty());
        let msgs = receive(&p, "baccio", None, None, 10, false).unwrap();
        assert_eq!(msgs.len(), 1);
        assert_eq!(msgs[0].content, "ciao");
    }

    #[test]
    fn broadcast_visible_to_all() {
        let (p, n) = setup();
        broadcast(&p, &n, "elena", "hello all", "text", None, 100).unwrap();
        let msgs = receive(&p, "anyone", None, None, 10, false).unwrap();
        assert_eq!(msgs.len(), 1);
    }

    #[test]
    fn rate_limit_enforced() {
        let (p, n) = setup();
        for i in 0..5 {
            send(&p, &n, "spammer", "target", &format!("msg{i}"), "text", 0, 5).unwrap();
        }
        let err = send(&p, &n, "spammer", "target", "one more", "text", 0, 5);
        assert!(matches!(err, Err(IpcError::RateLimited(_))));
    }

    #[test]
    fn history_returns_messages() {
        let (p, n) = setup();
        send(&p, &n, "a", "b", "first", "text", 0, 100).unwrap();
        send(&p, &n, "b", "a", "reply", "text", 0, 100).unwrap();
        let msgs = history(&p, Some("a"), None, 10, None).unwrap();
        assert_eq!(msgs.len(), 2);
    }
}
