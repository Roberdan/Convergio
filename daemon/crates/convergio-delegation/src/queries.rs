//! DB query and update helpers for delegation records.

use crate::types::{DelegationRecord, DelegationStatus, DelegationStep};
use convergio_db::pool::ConnPool;
use rusqlite::Connection;

type BoxErr = Box<dyn std::error::Error + Send + Sync>;

const COLS: &str = "id, delegation_id, plan_id, peer_name, status, current_step, \
    source_path, remote_path, error_message, started_at, completed_at";

/// Update delegation status and step in the DB via pool.
pub fn update_delegation_status(
    pool: &ConnPool,
    delegation_id: &str,
    status: &DelegationStatus,
    step: &DelegationStep,
) -> Result<(), BoxErr> {
    let conn = pool.get()?;
    update_delegation_status_conn(&conn, delegation_id, status, step)
}

/// Update delegation status using a direct connection.
pub fn update_delegation_status_conn(
    conn: &Connection,
    delegation_id: &str,
    status: &DelegationStatus,
    step: &DelegationStep,
) -> Result<(), BoxErr> {
    let status_str = status.to_string();
    let step_str = step.to_string();
    let error_msg = if let DelegationStatus::Failed(msg) = status {
        Some(msg.clone())
    } else {
        None
    };
    conn.execute(
        "UPDATE delegations SET status = ?1, current_step = ?2, error_message = ?3 \
         WHERE delegation_id = ?4",
        rusqlite::params![status_str, step_str, error_msg, delegation_id],
    )?;
    Ok(())
}

/// Set the remote_path field on a delegation record.
pub fn update_remote_path(
    pool: &ConnPool,
    delegation_id: &str,
    remote_path: &str,
) -> Result<(), BoxErr> {
    let conn = pool.get()?;
    conn.execute(
        "UPDATE delegations SET remote_path = ?1 WHERE delegation_id = ?2",
        rusqlite::params![remote_path, delegation_id],
    )?;
    Ok(())
}

/// Mark a delegation as completed with current timestamp.
pub fn complete_delegation(pool: &ConnPool, delegation_id: &str) -> Result<(), BoxErr> {
    let conn = pool.get()?;
    conn.execute(
        "UPDATE delegations SET completed_at = datetime('now') WHERE delegation_id = ?1",
        rusqlite::params![delegation_id],
    )?;
    Ok(())
}

/// Get a single delegation by its delegation_id.
pub fn get_delegation(conn: &Connection, id: &str) -> Option<DelegationRecord> {
    conn.query_row(
        &format!("SELECT {COLS} FROM delegations WHERE delegation_id = ?1"),
        rusqlite::params![id],
        map_row,
    )
    .ok()
}

/// List delegations with optional plan_id filter.
pub fn list_delegations(
    conn: &Connection,
    plan_id: Option<i64>,
    limit: u32,
) -> Vec<DelegationRecord> {
    if let Some(pid) = plan_id {
        let sql = format!(
            "SELECT {COLS} FROM delegations WHERE plan_id=?1 ORDER BY started_at DESC LIMIT ?2"
        );
        let Ok(mut stmt) = conn.prepare(&sql) else {
            return vec![];
        };
        stmt.query_map(rusqlite::params![pid, limit], map_row)
            .map(|rows| rows.filter_map(|r| r.ok()).collect())
            .unwrap_or_default()
    } else {
        let sql = format!("SELECT {COLS} FROM delegations ORDER BY started_at DESC LIMIT ?1");
        let Ok(mut stmt) = conn.prepare(&sql) else {
            return vec![];
        };
        stmt.query_map(rusqlite::params![limit], map_row)
            .map(|rows| rows.filter_map(|r| r.ok()).collect())
            .unwrap_or_default()
    }
}

fn map_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<DelegationRecord> {
    Ok(DelegationRecord {
        id: row.get(0)?,
        delegation_id: row.get(1)?,
        plan_id: row.get(2)?,
        peer_name: row.get(3)?,
        status: row.get(4)?,
        current_step: row.get(5)?,
        source_path: row.get(6)?,
        remote_path: row.get(7)?,
        error_message: row.get(8)?,
        started_at: row.get(9)?,
        completed_at: row.get(10)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup_conn() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    fn insert(conn: &Connection, id: &str, plan: i64, peer: &str) {
        conn.execute(
            "INSERT INTO delegations (delegation_id,plan_id,peer_name,source_path) \
             VALUES(?1,?2,?3,'/tmp')",
            rusqlite::params![id, plan, peer],
        )
        .unwrap();
    }

    #[test]
    fn update_and_get_status() {
        let conn = setup_conn();
        insert(&conn, "del-001", 1, "studio-mac");
        update_delegation_status_conn(
            &conn,
            "del-001",
            &DelegationStatus::CopyingFiles,
            &DelegationStep::FileCopy,
        )
        .unwrap();
        let rec = get_delegation(&conn, "del-001").unwrap();
        assert_eq!(rec.status, "copying_files");
        assert_eq!(rec.current_step, "file_copy");
    }

    #[test]
    fn get_not_found() {
        let conn = setup_conn();
        assert!(get_delegation(&conn, "nonexistent").is_none());
    }

    #[test]
    fn list_all_and_by_plan() {
        let conn = setup_conn();
        insert(&conn, "del-001", 1, "studio-mac");
        insert(&conn, "del-002", 2, "linux-box");
        assert_eq!(list_delegations(&conn, None, 50).len(), 2);
        assert_eq!(list_delegations(&conn, Some(1), 50).len(), 1);
    }

    #[test]
    fn failed_status_persists_error() {
        let conn = setup_conn();
        insert(&conn, "del-003", 3, "studio-mac");
        let status = DelegationStatus::Failed("ssh timeout".into());
        update_delegation_status_conn(&conn, "del-003", &status, &DelegationStep::Spawn).unwrap();
        let rec = get_delegation(&conn, "del-003").unwrap();
        assert!(rec.status.starts_with("failed"));
        assert_eq!(rec.error_message.as_deref(), Some("ssh timeout"));
    }
}
