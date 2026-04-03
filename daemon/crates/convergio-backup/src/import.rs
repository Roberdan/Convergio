//! Org data import — load a previously exported JSON bundle.
//!
//! Reads the export bundle, validates metadata, and inserts rows
//! into the appropriate tables. Skips rows that already exist (by PK).

use crate::types::{BackupResult, OrgExportMeta};
use convergio_db::pool::ConnPool;
use serde_json::Value;
use std::path::Path;
use tracing::{info, warn};

/// Import result summary.
#[derive(Debug, Clone, serde::Serialize)]
pub struct ImportResult {
    pub org_id: String,
    pub tables_imported: Vec<String>,
    pub rows_inserted: Vec<(String, i64)>,
    pub rows_skipped: Vec<(String, i64)>,
}

/// Import org data from an export bundle file.
pub fn import_org_data(pool: &ConnPool, bundle_path: &Path) -> BackupResult<ImportResult> {
    let content = std::fs::read_to_string(bundle_path)?;
    let bundle: Value = serde_json::from_str(&content)?;

    let meta: OrgExportMeta = serde_json::from_value(bundle["meta"].clone())?;

    let data = bundle["data"]
        .as_object()
        .unwrap_or(&serde_json::Map::new())
        .clone();

    let conn = pool.get()?;
    let mut tables_imported = Vec::new();
    let mut rows_inserted = Vec::new();
    let mut rows_skipped = Vec::new();

    for (table, rows_val) in &data {
        let rows = match rows_val.as_array() {
            Some(arr) => arr,
            None => continue,
        };

        // Check table exists
        let exists: bool = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='table' AND name=?1",
                rusqlite::params![table],
                |r| r.get::<_, i64>(0),
            )
            .map(|c| c > 0)?;

        if !exists {
            warn!(table = %table, "table does not exist, skipping import");
            continue;
        }

        let (inserted, skipped) = import_table_rows(&conn, table, rows)?;
        tables_imported.push(table.clone());
        rows_inserted.push((table.clone(), inserted));
        rows_skipped.push((table.clone(), skipped));
    }

    info!(
        org = %meta.org_id,
        tables = tables_imported.len(),
        "org data imported"
    );

    Ok(ImportResult {
        org_id: meta.org_id,
        tables_imported,
        rows_inserted,
        rows_skipped,
    })
}

/// Insert rows into a table, skipping conflicts (duplicate PKs).
fn import_table_rows(
    conn: &rusqlite::Connection,
    table: &str,
    rows: &[Value],
) -> BackupResult<(i64, i64)> {
    let mut inserted = 0i64;
    let mut skipped = 0i64;

    for row in rows {
        let obj = match row.as_object() {
            Some(o) => o,
            None => continue,
        };

        let columns: Vec<&str> = obj.keys().map(|k| k.as_str()).collect();
        let placeholders: Vec<String> = (1..=columns.len()).map(|i| format!("?{i}")).collect();

        let sql = format!(
            "INSERT OR IGNORE INTO {} ({}) VALUES ({})",
            table,
            columns.join(", "),
            placeholders.join(", "),
        );

        let values: Vec<Box<dyn rusqlite::ToSql>> = obj.values().map(json_to_tosql).collect();

        let refs: Vec<&dyn rusqlite::ToSql> = values.iter().map(|b| b.as_ref()).collect();

        let changed = conn.execute(&sql, refs.as_slice())?;
        if changed > 0 {
            inserted += 1;
        } else {
            skipped += 1;
        }
    }

    Ok((inserted, skipped))
}

/// Convert a serde_json Value to a boxed ToSql for rusqlite.
fn json_to_tosql(val: &Value) -> Box<dyn rusqlite::ToSql> {
    match val {
        Value::String(s) => Box::new(s.clone()),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Box::new(i)
            } else if let Some(f) = n.as_f64() {
                Box::new(f)
            } else {
                Box::new(n.to_string())
            }
        }
        Value::Bool(b) => Box::new(*b as i32),
        Value::Null => Box::new(rusqlite::types::Null),
        other => Box::new(other.to_string()),
    }
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
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS ipc_agents (
                id TEXT PRIMARY KEY, name TEXT, org_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )",
        )
        .unwrap();
        drop(conn);
        pool
    }

    fn write_bundle(dir: &Path, org_id: &str, data: Value) -> std::path::PathBuf {
        let bundle = serde_json::json!({
            "meta": {
                "org_id": org_id,
                "org_name": "Test Corp",
                "exported_at": "2026-04-03T00:00:00Z",
                "node": "test-node",
                "tables": ["ipc_agents"],
                "row_counts": [["ipc_agents", 1]],
                "version": "0.1.0"
            },
            "data": data,
        });
        let path = dir.join("import-test.json");
        std::fs::write(&path, serde_json::to_string_pretty(&bundle).unwrap()).unwrap();
        path
    }

    #[test]
    fn import_inserts_rows() {
        let pool = setup_pool();
        let tmp = tempfile::tempdir().unwrap();
        let data = serde_json::json!({
            "ipc_agents": [
                {"id": "a1", "name": "Elena", "org_id": "org-legal"}
            ]
        });
        let path = write_bundle(tmp.path(), "org-legal", data);

        let result = import_org_data(&pool, &path).unwrap();
        assert_eq!(result.rows_inserted[0].1, 1);

        let conn = pool.get().unwrap();
        let count: i64 = conn
            .query_row("SELECT COUNT(*) FROM ipc_agents", [], |r| r.get(0))
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn import_skips_duplicates() {
        let pool = setup_pool();
        let conn = pool.get().unwrap();
        conn.execute(
            "INSERT INTO ipc_agents VALUES ('a1', 'Existing', 'org-legal', \
             datetime('now'))",
            [],
        )
        .unwrap();
        drop(conn);

        let tmp = tempfile::tempdir().unwrap();
        let data = serde_json::json!({
            "ipc_agents": [
                {"id": "a1", "name": "Elena", "org_id": "org-legal"}
            ]
        });
        let path = write_bundle(tmp.path(), "org-legal", data);

        let result = import_org_data(&pool, &path).unwrap();
        assert_eq!(result.rows_skipped[0].1, 1);
        assert_eq!(result.rows_inserted[0].1, 0);
    }

    #[test]
    fn import_ignores_missing_tables() {
        let pool = setup_pool();
        let tmp = tempfile::tempdir().unwrap();
        let data = serde_json::json!({
            "nonexistent_table": [{"id": "x"}]
        });
        let path = write_bundle(tmp.path(), "org-test", data);

        let result = import_org_data(&pool, &path).unwrap();
        assert!(result.tables_imported.is_empty());
    }
}
