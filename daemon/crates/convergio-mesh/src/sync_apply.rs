//! Sync data exchange: export local changes, apply remote changes.
//!
//! Extracted from sync.rs to stay under 250-line limit.

use rusqlite::Connection;

use crate::types::SyncChange;

/// Export rows with updated_at > since. Returns SyncChange vec.
/// Tables that don't exist are silently skipped.
pub fn export_changes_since(
    conn: &Connection,
    table: &str,
    since: Option<&str>,
) -> Result<Vec<SyncChange>, rusqlite::Error> {
    if !table.chars().all(|c| c.is_ascii_alphanumeric() || c == '_') {
        return Err(rusqlite::Error::InvalidParameterName(
            "invalid table name".to_string(),
        ));
    }
    let exists: bool = conn
        .prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1")?
        .exists(rusqlite::params![table])?;
    if !exists {
        return Ok(vec![]);
    }

    let sql = match since {
        Some(_) => format!(
            "SELECT id, * FROM \"{table}\" \
             WHERE REPLACE(updated_at,'T',' ') > ?1 ORDER BY id"
        ),
        None => format!("SELECT id, * FROM \"{table}\" ORDER BY id"),
    };
    let mut stmt = conn.prepare(&sql)?;
    let col_count = stmt.column_count();
    let col_names: Vec<String> = (0..col_count)
        .map(|i| stmt.column_name(i).unwrap_or("").to_string())
        .collect();

    let params: Vec<Box<dyn rusqlite::types::ToSql>> = match since {
        Some(ts) => vec![Box::new(ts.replace('T', " "))],
        None => vec![],
    };
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();

    let rows = stmt.query_map(param_refs.as_slice(), |row| {
        let pk: i64 = row.get(0)?;
        let mut data = serde_json::Map::new();
        for (i, name) in col_names.iter().enumerate().skip(1) {
            let val: rusqlite::types::Value = row.get(i)?;
            data.insert(name.clone(), sqlite_to_json(val));
        }
        Ok(SyncChange {
            table_name: table.to_string(),
            pk,
            data: serde_json::Value::Object(data),
        })
    })?;
    rows.collect()
}

fn sqlite_to_json(val: rusqlite::types::Value) -> serde_json::Value {
    match val {
        rusqlite::types::Value::Null => serde_json::Value::Null,
        rusqlite::types::Value::Integer(i) => serde_json::json!(i),
        rusqlite::types::Value::Real(f) => serde_json::json!(f),
        rusqlite::types::Value::Text(s) => serde_json::json!(s),
        rusqlite::types::Value::Blob(b) => {
            use base64::{engine::general_purpose::STANDARD, Engine};
            serde_json::json!(STANDARD.encode(&b))
        }
    }
}

/// Apply remote changes using INSERT OR REPLACE.
/// Disables foreign keys during import to avoid ordering issues.
pub fn apply_changes(conn: &Connection, changes: &[SyncChange]) -> Result<usize, rusqlite::Error> {
    if changes.is_empty() {
        return Ok(0);
    }
    let mut applied = 0;
    conn.execute("PRAGMA foreign_keys = OFF", [])?;
    for change in changes {
        let Some(obj) = change.data.as_object() else {
            continue;
        };
        let cols: Vec<&str> = obj.keys().map(|k| k.as_str()).collect();
        let placeholders: Vec<String> = (1..=cols.len()).map(|i| format!("?{i}")).collect();
        let sql = format!(
            "INSERT OR REPLACE INTO \"{}\" ({}) VALUES ({})",
            change.table_name,
            cols.join(", "),
            placeholders.join(", ")
        );
        let vals: Vec<String> = obj.values().map(json_to_sql_string).collect();
        let params: Vec<&dyn rusqlite::types::ToSql> = vals
            .iter()
            .map(|v| v as &dyn rusqlite::types::ToSql)
            .collect();
        if conn.execute(&sql, params.as_slice()).is_ok() {
            applied += 1;
        }
    }
    conn.execute("PRAGMA foreign_keys = ON", [])?;
    Ok(applied)
}

fn json_to_sql_string(v: &serde_json::Value) -> String {
    match v {
        serde_json::Value::String(s) => s.clone(),
        serde_json::Value::Null => String::new(),
        other => other.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn export_nonexistent_table_returns_empty() {
        let conn = Connection::open_in_memory().unwrap();
        let changes = export_changes_since(&conn, "nonexistent", None).unwrap();
        assert!(changes.is_empty());
    }

    #[test]
    fn export_rejects_invalid_table_name() {
        let conn = Connection::open_in_memory().unwrap();
        let result = export_changes_since(&conn, "drop;--", None);
        assert!(result.is_err());
    }

    #[test]
    fn apply_empty_returns_zero() {
        let conn = Connection::open_in_memory().unwrap();
        assert_eq!(apply_changes(&conn, &[]).unwrap(), 0);
    }

    #[test]
    fn export_and_apply_roundtrip() {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE test_sync (
                id INTEGER PRIMARY KEY,
                name TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO test_sync (id, name) VALUES (1, 'alpha');
            INSERT INTO test_sync (id, name) VALUES (2, 'beta');",
        )
        .unwrap();
        let changes = export_changes_since(&conn, "test_sync", None).unwrap();
        assert_eq!(changes.len(), 2);

        let conn2 = Connection::open_in_memory().unwrap();
        conn2
            .execute_batch(
                "CREATE TABLE test_sync (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    updated_at TEXT
                );",
            )
            .unwrap();
        let applied = apply_changes(&conn2, &changes).unwrap();
        assert_eq!(applied, 2);
    }
}
