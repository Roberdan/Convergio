//! Retention policy engine — auto-purge expired data.
//!
//! Never deletes silently: every purge is logged to backup_purge_log
//! and emits a PurgeEvent for SSE streaming.

use crate::types::{BackupResult, PurgeEvent, RetentionRule};
use convergio_db::pool::ConnPool;
use rusqlite::params;
use tracing::{info, warn};

/// Load retention rules from the database.
/// Falls back to default rules if none are configured.
pub fn load_rules(pool: &ConnPool) -> BackupResult<Vec<RetentionRule>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT table_name, timestamp_column, max_age_days \
         FROM backup_retention_rules WHERE org_id = '__global__'",
    )?;
    let rules: Vec<RetentionRule> = stmt
        .query_map([], |row| {
            Ok(RetentionRule {
                table: row.get(0)?,
                timestamp_column: row.get(1)?,
                max_age_days: row.get(2)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    if rules.is_empty() {
        return Ok(crate::types::default_retention_rules());
    }
    Ok(rules)
}

/// Load org-specific retention rules (override defaults).
pub fn load_org_rules(pool: &ConnPool, org_id: &str) -> BackupResult<Vec<RetentionRule>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT table_name, timestamp_column, max_age_days \
         FROM backup_retention_rules WHERE org_id = ?1",
    )?;
    let rules: Vec<RetentionRule> = stmt
        .query_map(params![org_id], |row| {
            Ok(RetentionRule {
                table: row.get(0)?,
                timestamp_column: row.get(1)?,
                max_age_days: row.get(2)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(rules)
}

/// Save a retention rule to the database.
pub fn save_rule(pool: &ConnPool, rule: &RetentionRule, org_id: Option<&str>) -> BackupResult<()> {
    let conn = pool.get()?;
    let effective_org = org_id.unwrap_or("__global__");
    conn.execute(
        "INSERT INTO backup_retention_rules \
         (table_name, timestamp_column, max_age_days, org_id) \
         VALUES (?1, ?2, ?3, ?4) \
         ON CONFLICT(table_name, org_id) DO UPDATE SET \
         timestamp_column = excluded.timestamp_column, \
         max_age_days = excluded.max_age_days",
        params![
            rule.table,
            rule.timestamp_column,
            rule.max_age_days,
            effective_org
        ],
    )?;
    Ok(())
}

/// Execute purge for a single retention rule. Returns a PurgeEvent.
pub fn purge_table(pool: &ConnPool, rule: &RetentionRule) -> BackupResult<PurgeEvent> {
    let conn = pool.get()?;
    let cutoff = format!("-{} days", rule.max_age_days);

    // Check if table exists before attempting purge
    let exists: bool = conn
        .query_row(
            "SELECT COUNT(*) FROM sqlite_master \
             WHERE type='table' AND name=?1",
            params![rule.table],
            |r| r.get::<_, i64>(0),
        )
        .map(|c| c > 0)?;

    if !exists {
        warn!(table = %rule.table, "table does not exist, skipping purge");
        return Ok(PurgeEvent {
            table: rule.table.clone(),
            rows_deleted: 0,
            cutoff_date: cutoff,
            executed_at: chrono::Utc::now().to_rfc3339(),
        });
    }

    // Count rows to be deleted (for logging)
    let sql_count = format!(
        "SELECT COUNT(*) FROM {} WHERE {} < datetime('now', ?1)",
        rule.table, rule.timestamp_column,
    );
    let count: i64 = conn.query_row(&sql_count, params![cutoff], |r| r.get(0))?;

    if count > 0 {
        let sql_delete = format!(
            "DELETE FROM {} WHERE {} < datetime('now', ?1)",
            rule.table, rule.timestamp_column,
        );
        conn.execute(&sql_delete, params![cutoff])?;
    }

    let now = chrono::Utc::now().to_rfc3339();
    // Log the purge
    conn.execute(
        "INSERT INTO backup_purge_log (table_name, rows_deleted, cutoff_date) \
         VALUES (?1, ?2, ?3)",
        params![rule.table, count, cutoff],
    )?;

    info!(table = %rule.table, rows = count, "retention purge completed");

    Ok(PurgeEvent {
        table: rule.table.clone(),
        rows_deleted: count,
        cutoff_date: cutoff,
        executed_at: now,
    })
}

/// Run auto-purge for all configured retention rules.
pub fn run_auto_purge(pool: &ConnPool) -> BackupResult<Vec<PurgeEvent>> {
    let rules = load_rules(pool)?;
    let mut events = Vec::new();
    for rule in &rules {
        match purge_table(pool, rule) {
            Ok(ev) => events.push(ev),
            Err(e) => {
                warn!(table = %rule.table, err = %e, "purge failed for table");
            }
        }
    }
    Ok(events)
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
            "CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY, msg TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )",
        )
        .unwrap();
        drop(conn);
        pool
    }

    #[test]
    fn load_rules_returns_defaults_when_empty() {
        let pool = setup_pool();
        let rules = load_rules(&pool).unwrap();
        assert_eq!(rules.len(), 2);
    }

    #[test]
    fn save_and_load_custom_rule() {
        let pool = setup_pool();
        let rule = RetentionRule {
            table: "audit_log".into(),
            timestamp_column: "created_at".into(),
            max_age_days: 90,
        };
        save_rule(&pool, &rule, None).unwrap();
        let rules = load_rules(&pool).unwrap();
        assert_eq!(rules.len(), 1);
        assert_eq!(rules[0].max_age_days, 90);
    }

    #[test]
    fn purge_table_deletes_old_rows() {
        let pool = setup_pool();
        let conn = pool.get().unwrap();
        // Insert old and new rows
        conn.execute(
            "INSERT INTO audit_log (msg, created_at) \
             VALUES ('old', datetime('now', '-400 days'))",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO audit_log (msg, created_at) \
             VALUES ('new', datetime('now'))",
            [],
        )
        .unwrap();
        drop(conn);

        let rule = RetentionRule {
            table: "audit_log".into(),
            timestamp_column: "created_at".into(),
            max_age_days: 365,
        };
        let event = purge_table(&pool, &rule).unwrap();
        assert_eq!(event.rows_deleted, 1);

        let conn = pool.get().unwrap();
        let remaining: i64 = conn
            .query_row("SELECT COUNT(*) FROM audit_log", [], |r| r.get(0))
            .unwrap();
        assert_eq!(remaining, 1);
    }

    #[test]
    fn purge_nonexistent_table_returns_zero() {
        let pool = setup_pool();
        let rule = RetentionRule {
            table: "nonexistent_table".into(),
            timestamp_column: "created_at".into(),
            max_age_days: 7,
        };
        let event = purge_table(&pool, &rule).unwrap();
        assert_eq!(event.rows_deleted, 0);
    }

    #[test]
    fn run_auto_purge_processes_all_rules() {
        let pool = setup_pool();
        let events = run_auto_purge(&pool).unwrap();
        // Default rules: audit_log (exists) + ipc_messages (does not)
        assert_eq!(events.len(), 2);
    }
}
