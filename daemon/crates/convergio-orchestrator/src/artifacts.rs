// Artifact storage and retrieval for non-code project outputs.
// WHY: Non-code projects (reports, analysis, documents) need artifact tracking
// beyond git commits and test evidence.

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Artifact {
    pub id: i64,
    pub task_id: i64,
    pub plan_id: i64,
    pub name: String,
    pub artifact_type: String,
    pub path: String,
    pub size_bytes: i64,
    pub mime_type: Option<String>,
    pub content_hash: Option<String>,
    pub created_at: String,
}

/// Record a new artifact in the DB.
pub fn record_artifact(
    conn: &Connection,
    task_id: i64,
    plan_id: i64,
    name: &str,
    artifact_type: &str,
    path: &str,
    size_bytes: i64,
) -> Result<i64, rusqlite::Error> {
    record_artifact_full(
        conn,
        task_id,
        plan_id,
        name,
        artifact_type,
        path,
        size_bytes,
        None,
        None,
    )
}

/// Record an artifact with optional mime_type and content_hash.
pub fn record_artifact_full(
    conn: &Connection,
    task_id: i64,
    plan_id: i64,
    name: &str,
    artifact_type: &str,
    path: &str,
    size_bytes: i64,
    mime_type: Option<&str>,
    content_hash: Option<&str>,
) -> Result<i64, rusqlite::Error> {
    conn.execute(
        "INSERT INTO artifacts \
         (task_id, plan_id, name, artifact_type, path, size_bytes, mime_type, content_hash) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            task_id,
            plan_id,
            name,
            artifact_type,
            path,
            size_bytes,
            mime_type,
            content_hash
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// List artifacts for a plan.
pub fn list_artifacts(conn: &Connection, plan_id: i64) -> Vec<Artifact> {
    let mut stmt = match conn.prepare(
        "SELECT id, task_id, plan_id, name, artifact_type, path, \
         size_bytes, mime_type, content_hash, created_at \
         FROM artifacts WHERE plan_id = ?1 ORDER BY id",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map(params![plan_id], map_artifact)
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

/// Get a single artifact by ID.
pub fn get_artifact(conn: &Connection, id: i64) -> Option<Artifact> {
    conn.query_row(
        "SELECT id, task_id, plan_id, name, artifact_type, path, \
         size_bytes, mime_type, content_hash, created_at \
         FROM artifacts WHERE id = ?1",
        params![id],
        map_artifact,
    )
    .ok()
}

/// List artifacts for a specific task.
pub fn list_task_artifacts(conn: &Connection, task_id: i64) -> Vec<Artifact> {
    let mut stmt = match conn.prepare(
        "SELECT id, task_id, plan_id, name, artifact_type, path, \
         size_bytes, mime_type, content_hash, created_at \
         FROM artifacts WHERE task_id = ?1 ORDER BY id",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map(params![task_id], map_artifact)
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

fn map_artifact(r: &rusqlite::Row) -> rusqlite::Result<Artifact> {
    Ok(Artifact {
        id: r.get(0)?,
        task_id: r.get(1)?,
        plan_id: r.get(2)?,
        name: r.get(3)?,
        artifact_type: r.get(4)?,
        path: r.get(5)?,
        size_bytes: r.get(6)?,
        mime_type: r.get(7)?,
        content_hash: r.get(8)?,
        created_at: r.get(9)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        for m in crate::schema_tracking::tracking_migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        // Seed plan + task
        conn.execute(
            "INSERT INTO plans(id, project_id, name) VALUES (1, 'proj-alpha', 'Report Plan')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks(id, plan_id, status) VALUES (10, 1, 'in_progress')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn test_record_and_list_artifacts() {
        let conn = setup();
        let id1 = record_artifact(
            &conn,
            10,
            1,
            "quarterly.pdf",
            "pdf",
            "1/quarterly.pdf",
            4096,
        )
        .unwrap();
        let id2 =
            record_artifact(&conn, 10, 1, "summary.md", "document", "1/summary.md", 1024).unwrap();
        assert!(id1 > 0);
        assert!(id2 > id1);

        let arts = list_artifacts(&conn, 1);
        assert_eq!(arts.len(), 2);
        assert_eq!(arts[0].name, "quarterly.pdf");
        assert_eq!(arts[1].name, "summary.md");
    }

    #[test]
    fn test_list_task_artifacts() {
        let conn = setup();
        // Add a second task
        conn.execute(
            "INSERT INTO tasks(id, plan_id, status) VALUES (20, 1, 'pending')",
            [],
        )
        .unwrap();
        record_artifact(&conn, 10, 1, "report.pdf", "pdf", "1/report.pdf", 2048).unwrap();
        record_artifact(&conn, 20, 1, "chart.png", "screenshot", "1/chart.png", 8192).unwrap();

        let task10 = list_task_artifacts(&conn, 10);
        assert_eq!(task10.len(), 1);
        assert_eq!(task10[0].name, "report.pdf");

        let task20 = list_task_artifacts(&conn, 20);
        assert_eq!(task20.len(), 1);
        assert_eq!(task20[0].name, "chart.png");
    }

    #[test]
    fn test_get_artifact_by_id() {
        let conn = setup();
        let id =
            record_artifact(&conn, 10, 1, "deck.pptx", "bundle", "1/deck.pptx", 51200).unwrap();
        let art = get_artifact(&conn, id).unwrap();
        assert_eq!(art.name, "deck.pptx");
        assert_eq!(art.size_bytes, 51200);

        assert!(get_artifact(&conn, 9999).is_none());
    }
}
