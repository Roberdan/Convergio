// Artifact bundle management — group artifacts into deliverables.
// WHY: Production workflows need to package multiple artifacts into a single
// reviewable unit (report pack, evidence bundle, deliverable set).

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArtifactBundle {
    pub id: i64,
    pub plan_id: i64,
    pub name: String,
    pub bundle_type: String,
    pub status: String,
    pub created_at: String,
    pub published_at: Option<String>,
}

/// Create a new bundle for a plan.
pub fn create_bundle(
    conn: &Connection,
    plan_id: i64,
    name: &str,
    bundle_type: &str,
) -> Result<i64, rusqlite::Error> {
    conn.execute(
        "INSERT INTO artifact_bundles (plan_id, name, bundle_type) \
         VALUES (?1, ?2, ?3)",
        params![plan_id, name, bundle_type],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Add an artifact to a bundle (idempotent).
pub fn add_to_bundle(
    conn: &Connection,
    bundle_id: i64,
    artifact_id: i64,
) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT OR IGNORE INTO bundle_artifacts (bundle_id, artifact_id) \
         VALUES (?1, ?2)",
        params![bundle_id, artifact_id],
    )?;
    Ok(())
}

/// List bundles for a plan.
pub fn list_bundles(conn: &Connection, plan_id: i64) -> Vec<ArtifactBundle> {
    let mut stmt = match conn.prepare(
        "SELECT id, plan_id, name, bundle_type, status, created_at, published_at \
         FROM artifact_bundles WHERE plan_id = ?1 ORDER BY id",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map(params![plan_id], map_bundle)
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

/// Get a bundle with its artifact IDs.
pub fn get_bundle_with_artifacts(
    conn: &Connection,
    bundle_id: i64,
) -> Option<(ArtifactBundle, Vec<i64>)> {
    let bundle = conn
        .query_row(
            "SELECT id, plan_id, name, bundle_type, status, created_at, published_at \
             FROM artifact_bundles WHERE id = ?1",
            params![bundle_id],
            map_bundle,
        )
        .ok()?;

    let mut stmt = conn
        .prepare(
            "SELECT artifact_id FROM bundle_artifacts \
             WHERE bundle_id = ?1 ORDER BY artifact_id",
        )
        .ok()?;
    let ids: Vec<i64> = stmt
        .query_map(params![bundle_id], |r| r.get(0))
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default();
    Some((bundle, ids))
}

/// Transition bundle status (draft -> reviewed -> published).
pub fn update_bundle_status(
    conn: &Connection,
    bundle_id: i64,
    status: &str,
) -> Result<(), rusqlite::Error> {
    let published_clause = if status == "published" {
        ", published_at = datetime('now')"
    } else {
        ""
    };
    let sql = format!("UPDATE artifact_bundles SET status = ?1{published_clause} WHERE id = ?2");
    conn.execute(&sql, params![status, bundle_id])?;
    Ok(())
}

fn map_bundle(r: &rusqlite::Row) -> rusqlite::Result<ArtifactBundle> {
    Ok(ArtifactBundle {
        id: r.get(0)?,
        plan_id: r.get(1)?,
        name: r.get(2)?,
        bundle_type: r.get(3)?,
        status: r.get(4)?,
        created_at: r.get(5)?,
        published_at: r.get(6)?,
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
    fn test_create_and_list_bundles() {
        let conn = setup();
        let id1 = create_bundle(&conn, 1, "Q4 Deliverable", "deliverable").unwrap();
        let id2 = create_bundle(&conn, 1, "Evidence Pack", "evidence-pack").unwrap();
        assert!(id1 > 0);
        assert!(id2 > id1);

        let bundles = list_bundles(&conn, 1);
        assert_eq!(bundles.len(), 2);
        assert_eq!(bundles[0].name, "Q4 Deliverable");
        assert_eq!(bundles[1].bundle_type, "evidence-pack");
        assert_eq!(bundles[0].status, "draft");
    }

    #[test]
    fn test_add_artifact_to_bundle() {
        let conn = setup();
        let bundle_id = create_bundle(&conn, 1, "Report Bundle", "deliverable").unwrap();
        let art_id = crate::artifacts::record_artifact(
            &conn,
            10,
            1,
            "report.pdf",
            "pdf",
            "1/report.pdf",
            4096,
        )
        .unwrap();
        add_to_bundle(&conn, bundle_id, art_id).unwrap();
        // Idempotent — second insert should not fail
        add_to_bundle(&conn, bundle_id, art_id).unwrap();

        let (_, ids) = get_bundle_with_artifacts(&conn, bundle_id).unwrap();
        assert_eq!(ids, vec![art_id]);
    }

    #[test]
    fn test_bundle_status_transition() {
        let conn = setup();
        let id = create_bundle(&conn, 1, "Final Report", "report").unwrap();
        assert_eq!(list_bundles(&conn, 1)[0].status, "draft");

        update_bundle_status(&conn, id, "reviewed").unwrap();
        let (b, _) = get_bundle_with_artifacts(&conn, id).unwrap();
        assert_eq!(b.status, "reviewed");
        assert!(b.published_at.is_none());

        update_bundle_status(&conn, id, "published").unwrap();
        let (b, _) = get_bundle_with_artifacts(&conn, id).unwrap();
        assert_eq!(b.status, "published");
        assert!(b.published_at.is_some());
    }

    #[test]
    fn test_get_bundle_with_artifacts() {
        let conn = setup();
        let bundle_id = create_bundle(&conn, 1, "Mixed Pack", "deliverable").unwrap();
        let a1 =
            crate::artifacts::record_artifact(&conn, 10, 1, "doc.pdf", "pdf", "1/doc.pdf", 1024)
                .unwrap();
        let a2 = crate::artifacts::record_artifact(
            &conn,
            10,
            1,
            "screenshot.png",
            "image",
            "1/screenshot.png",
            2048,
        )
        .unwrap();
        add_to_bundle(&conn, bundle_id, a1).unwrap();
        add_to_bundle(&conn, bundle_id, a2).unwrap();

        let (bundle, ids) = get_bundle_with_artifacts(&conn, bundle_id).unwrap();
        assert_eq!(bundle.name, "Mixed Pack");
        assert_eq!(ids.len(), 2);
        assert!(ids.contains(&a1));
        assert!(ids.contains(&a2));

        // Non-existent bundle
        assert!(get_bundle_with_artifacts(&conn, 9999).is_none());
    }
}
