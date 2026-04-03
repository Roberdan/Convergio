//! Org data export — package all org data into a portable JSON bundle.
//!
//! Exports tasks, prompts, agents, billing records, and audit trail
//! for a single org. The bundle can be imported on another node.

use crate::types::{BackupResult, OrgExportMeta};
use convergio_db::pool::ConnPool;
use rusqlite::params;
use serde_json::{json, Value};
use std::path::Path;
use tracing::info;

/// Tables that store org-scoped data (column = org_id).
const ORG_TABLES: &[(&str, &str)] = &[
    ("ipc_agents", "org_id"),
    ("ipc_messages", "org_id"),
    ("ipc_budget_log", "org_id"),
];

/// Export all data for an org into a JSON file.
///
/// Scans known org-scoped tables, extracts rows matching the org_id,
/// and writes a self-describing JSON bundle to `dest_path`.
pub fn export_org_data(
    pool: &ConnPool,
    org_id: &str,
    org_name: &str,
    node: &str,
    dest_path: &Path,
) -> BackupResult<OrgExportMeta> {
    let conn = pool.get()?;
    let mut tables_exported = Vec::new();
    let mut row_counts = Vec::new();
    let mut data = serde_json::Map::new();

    for &(table, col) in ORG_TABLES {
        // Check if table exists
        let exists: bool = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='table' AND name=?1",
                params![table],
                |r| r.get::<_, i64>(0),
            )
            .map(|c| c > 0)?;

        if !exists {
            continue;
        }

        let rows = export_table_rows(&conn, table, col, org_id)?;
        let count = rows.len() as i64;
        if count > 0 {
            tables_exported.push(table.to_string());
            row_counts.push((table.to_string(), count));
            data.insert(table.to_string(), Value::Array(rows));
        }
    }

    let meta = OrgExportMeta {
        org_id: org_id.to_string(),
        org_name: org_name.to_string(),
        exported_at: chrono::Utc::now().to_rfc3339(),
        node: node.to_string(),
        tables: tables_exported,
        row_counts,
        version: env!("CARGO_PKG_VERSION").to_string(),
    };

    let bundle = json!({
        "meta": meta,
        "data": data,
    });

    if let Some(parent) = dest_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let json_str = serde_json::to_string_pretty(&bundle)?;
    std::fs::write(dest_path, json_str)?;

    info!(
        org = %org_id,
        tables = meta.tables.len(),
        path = %dest_path.display(),
        "org data exported"
    );
    Ok(meta)
}

/// Extract all rows for an org from a single table as JSON values.
fn export_table_rows(
    conn: &rusqlite::Connection,
    table: &str,
    org_col: &str,
    org_id: &str,
) -> BackupResult<Vec<Value>> {
    let sql = format!("SELECT * FROM {table} WHERE {org_col} = ?1");
    let mut stmt = conn.prepare(&sql)?;
    let col_names: Vec<String> = stmt.column_names().iter().map(|s| s.to_string()).collect();

    let rows = stmt.query_map(params![org_id], |row| {
        let mut obj = serde_json::Map::new();
        for (i, name) in col_names.iter().enumerate() {
            let val = row_value_at(row, i);
            obj.insert(name.clone(), val);
        }
        Ok(Value::Object(obj))
    })?;

    let mut result = Vec::new();
    for v in rows.flatten() {
        result.push(v);
    }
    Ok(result)
}

/// Extract a value from a rusqlite Row at a given index.
fn row_value_at(row: &rusqlite::Row<'_>, idx: usize) -> Value {
    if let Ok(v) = row.get::<_, String>(idx) {
        return Value::String(v);
    }
    if let Ok(v) = row.get::<_, i64>(idx) {
        return Value::Number(v.into());
    }
    if let Ok(v) = row.get::<_, f64>(idx) {
        return serde_json::Number::from_f64(v)
            .map(Value::Number)
            .unwrap_or(Value::Null);
    }
    Value::Null
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_pool() -> ConnPool {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        // Create a mock org-scoped table
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS ipc_agents (
                id TEXT PRIMARY KEY, name TEXT, org_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )",
        )
        .unwrap();
        conn.execute(
            "INSERT INTO ipc_agents VALUES ('a1', 'Elena', 'org-legal', \
             datetime('now'))",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO ipc_agents VALUES ('a2', 'Baccio', 'org-dev', \
             datetime('now'))",
            [],
        )
        .unwrap();
        drop(conn);
        pool
    }

    #[test]
    fn export_org_creates_bundle_file() {
        let pool = setup_pool();
        let tmp = tempfile::tempdir().unwrap();
        let dest = tmp.path().join("export.json");
        let meta = export_org_data(&pool, "org-legal", "Legal Corp", "test-node", &dest).unwrap();
        assert!(dest.exists());
        assert_eq!(meta.org_id, "org-legal");
        assert_eq!(meta.tables, vec!["ipc_agents"]);
        assert_eq!(meta.row_counts[0].1, 1);
    }

    #[test]
    fn export_empty_org_produces_empty_bundle() {
        let pool = setup_pool();
        let tmp = tempfile::tempdir().unwrap();
        let dest = tmp.path().join("export.json");
        let meta = export_org_data(&pool, "org-empty", "Empty Corp", "test-node", &dest).unwrap();
        assert!(meta.tables.is_empty());
    }

    #[test]
    fn export_bundle_is_valid_json() {
        let pool = setup_pool();
        let tmp = tempfile::tempdir().unwrap();
        let dest = tmp.path().join("export.json");
        export_org_data(&pool, "org-legal", "Legal Corp", "test-node", &dest).unwrap();
        let content = std::fs::read_to_string(&dest).unwrap();
        let parsed: Value = serde_json::from_str(&content).unwrap();
        assert!(parsed["meta"]["org_id"].is_string());
        assert!(parsed["data"]["ipc_agents"].is_array());
    }
}
