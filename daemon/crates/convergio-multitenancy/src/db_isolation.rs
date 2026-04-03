//! DB isolation — org table prefix enforcement.
//!
//! Each org gets prefixed tables. Cross-org access is blocked at query level.
//! The migration runner creates org-specific tables with the org prefix.

use crate::types::{OrgId, TenancyError};
use rusqlite::Connection;

/// Validate that a table name belongs to the requesting org.
/// Returns error if table prefix doesn't match org.
pub fn validate_table_access(org_id: &OrgId, table_name: &str) -> Result<(), TenancyError> {
    let prefix = org_id.table_prefix();
    // Shared tables (mt_*, _schema_registry) are always allowed
    if table_name.starts_with("mt_") || table_name.starts_with('_') {
        return Ok(());
    }
    // Org-prefixed tables must match
    if table_name.starts_with(&prefix) {
        return Ok(());
    }
    Err(TenancyError::IsolationViolation(format!(
        "org '{}' cannot access table '{}' (expected prefix '{}')",
        org_id, table_name, prefix
    )))
}

/// Create an org-prefixed table from a template.
/// Replaces `{prefix}` in the SQL with the org's table prefix.
pub fn create_org_table(
    conn: &Connection,
    org_id: &OrgId,
    template_sql: &str,
) -> Result<(), TenancyError> {
    let prefix = org_id.table_prefix();
    let sql = template_sql.replace("{prefix}", &prefix);
    conn.execute_batch(&sql)
        .map_err(|e| TenancyError::Db(format!("create org table: {e}")))?;
    tracing::info!(org = %org_id, prefix = %prefix, "created org-prefixed tables");
    Ok(())
}

/// List all tables belonging to an org (by prefix match).
pub fn list_org_tables(conn: &Connection, org_id: &OrgId) -> Result<Vec<String>, TenancyError> {
    let prefix = org_id.table_prefix();
    let mut stmt = conn
        .prepare(
            "SELECT name FROM sqlite_master \
             WHERE type = 'table' AND name LIKE ?1",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let pattern = format!("{prefix}%");
    let tables = stmt
        .query_map([&pattern], |row| row.get::<_, String>(0))
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(tables)
}

/// Drop all org-prefixed tables (for org deletion/cleanup).
pub fn drop_org_tables(conn: &Connection, org_id: &OrgId) -> Result<usize, TenancyError> {
    let tables = list_org_tables(conn, org_id)?;
    let count = tables.len();
    for table in &tables {
        let sql = format!("DROP TABLE IF EXISTS \"{table}\"");
        conn.execute_batch(&sql)
            .map_err(|e| TenancyError::Db(format!("drop {table}: {e}")))?;
    }
    tracing::info!(org = %org_id, dropped = count, "cleaned up org tables");
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_conn() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        conn
    }

    #[test]
    fn validate_own_prefix() {
        let org = OrgId("acme".into());
        assert!(validate_table_access(&org, "org_acme_tasks").is_ok());
    }

    #[test]
    fn reject_foreign_prefix() {
        let org = OrgId("acme".into());
        let result = validate_table_access(&org, "org_evil_tasks");
        assert!(result.is_err());
    }

    #[test]
    fn shared_tables_always_allowed() {
        let org = OrgId("acme".into());
        assert!(validate_table_access(&org, "mt_isolation_policies").is_ok());
        assert!(validate_table_access(&org, "_schema_registry").is_ok());
    }

    #[test]
    fn create_and_list_org_tables() {
        let conn = test_conn();
        let org = OrgId("acme".into());
        let template = "CREATE TABLE IF NOT EXISTS {prefix}tasks (id INTEGER PRIMARY KEY)";
        create_org_table(&conn, &org, template).unwrap();
        let tables = list_org_tables(&conn, &org).unwrap();
        assert_eq!(tables, vec!["org_acme_tasks"]);
    }

    #[test]
    fn drop_org_tables_cleans_up() {
        let conn = test_conn();
        let org = OrgId("cleanup".into());
        let tpl = "CREATE TABLE IF NOT EXISTS {prefix}data (id INTEGER PRIMARY KEY)";
        create_org_table(&conn, &org, tpl).unwrap();
        let dropped = drop_org_tables(&conn, &org).unwrap();
        assert_eq!(dropped, 1);
        let remaining = list_org_tables(&conn, &org).unwrap();
        assert!(remaining.is_empty());
    }
}
