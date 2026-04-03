//! Full-text search on events, agent messages, and audit log.
//!
//! Uses SQLite FTS5 for efficient text search across the obs_search
//! virtual table. Content is indexed when timeline events are recorded.

use rusqlite::{params, Connection};

use crate::types::SearchResult;

/// Index a piece of content for full-text search.
pub fn index_content(
    conn: &Connection,
    source: &str,
    event_type: &str,
    actor: &str,
    summary: &str,
    details: &str,
) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT INTO obs_search (source, event_type, actor, summary, details) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![source, event_type, actor, summary, details],
    )?;
    Ok(())
}

/// Run a full-text search query. Returns results ranked by relevance.
pub fn search(
    conn: &Connection,
    query: &str,
    limit: u32,
) -> Result<Vec<SearchResult>, rusqlite::Error> {
    let limit = limit.min(200);
    let mut stmt = conn.prepare(
        "SELECT rowid, source, snippet(obs_search, 3, '<b>', '</b>', '...', 32), \
         rank, '' AS created_at \
         FROM obs_search WHERE obs_search MATCH ?1 \
         ORDER BY rank LIMIT ?2",
    )?;
    let rows = stmt.query_map(params![query, limit], |row| {
        Ok(SearchResult {
            id: row.get(0)?,
            source: row.get(1)?,
            snippet: row.get(2)?,
            score: row.get::<_, f64>(3)?.abs(),
            created_at: row.get(4)?,
        })
    })?;
    rows.collect()
}

/// Count total indexed documents.
pub fn indexed_count(conn: &Connection) -> Result<i64, rusqlite::Error> {
    conn.query_row("SELECT COUNT(*) FROM obs_search", [], |r| r.get(0))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_db() -> convergio_db::pool::PooledConn {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(
            &conn,
            "observatory",
            &crate::schema::migrations(),
        )
        .unwrap();
        conn
    }

    #[test]
    fn index_and_search() {
        let conn = setup_db();
        index_content(
            &conn,
            "orchestrator",
            "task_completed",
            "Elena",
            "Review of contract section 4 completed",
            "Legal review passed all checks",
        )
        .unwrap();
        index_content(
            &conn,
            "agent",
            "message_sent",
            "Baccio",
            "Code review for authentication module",
            "Found 3 issues in auth middleware",
        )
        .unwrap();

        let results = search(&conn, "review", 10).unwrap();
        assert_eq!(results.len(), 2);

        let results = search(&conn, "contract", 10).unwrap();
        assert_eq!(results.len(), 1);
        assert!(results[0].snippet.contains("contract"));
    }

    #[test]
    fn indexed_count_tracks_documents() {
        let conn = setup_db();
        assert_eq!(indexed_count(&conn).unwrap(), 0);
        index_content(&conn, "system", "boot", "daemon", "System started", "").unwrap();
        assert_eq!(indexed_count(&conn).unwrap(), 1);
    }

    #[test]
    fn search_limit_respected() {
        let conn = setup_db();
        for i in 0..10 {
            index_content(
                &conn,
                "system",
                "event",
                "daemon",
                &format!("Deploy event number {i}"),
                "",
            )
            .unwrap();
        }
        let results = search(&conn, "deploy", 3).unwrap();
        assert_eq!(results.len(), 3);
    }
}
