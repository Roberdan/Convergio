//! High-level transfer operations — DB persistence and querying.

use crate::types::{TransferRecord, TransferRequest, TransferResult, TransferStatus};
use rusqlite::Connection;

/// Insert a completed transfer into the file_transfers table.
pub fn record_transfer(
    conn: &Connection,
    result: &TransferResult,
    req: &TransferRequest,
) -> Result<i64, rusqlite::Error> {
    let (status_str, error_msg) = match &result.status {
        TransferStatus::Success => ("success".to_string(), None),
        TransferStatus::Failed(msg) => ("failed".to_string(), Some(msg.clone())),
        TransferStatus::PartialSuccess(msg) => ("partial".to_string(), Some(msg.clone())),
    };

    conn.execute(
        "INSERT INTO file_transfers \
         (peer_name, direction, source_path, dest_path, \
          bytes_transferred, files_count, duration_ms, status, error_message) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        rusqlite::params![
            result.peer_name,
            req.direction.to_string(),
            req.source_path,
            req.dest_path,
            result.bytes_transferred as i64,
            result.files_count as i64,
            result.duration_ms as i64,
            status_str,
            error_msg,
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// List transfers with optional peer filter and limit.
pub fn list_transfers(
    conn: &Connection,
    peer: Option<&str>,
    limit: u32,
) -> Result<Vec<TransferRecord>, rusqlite::Error> {
    let sql = match peer {
        Some(_) => {
            "SELECT id, peer_name, direction, source_path, dest_path, \
                    bytes_transferred, files_count, duration_ms, status, \
                    error_message, created_at \
             FROM file_transfers WHERE peer_name = ?1 \
             ORDER BY created_at DESC LIMIT ?2"
        }
        None => {
            "SELECT id, peer_name, direction, source_path, dest_path, \
                    bytes_transferred, files_count, duration_ms, status, \
                    error_message, created_at \
             FROM file_transfers \
             ORDER BY created_at DESC LIMIT ?1"
        }
    };

    let mut stmt = conn.prepare(sql)?;
    let rows = if let Some(p) = peer {
        stmt.query_map(rusqlite::params![p, limit], map_row)?
    } else {
        stmt.query_map(rusqlite::params![limit], map_row)?
    };
    rows.collect()
}

/// Get a single transfer by ID.
pub fn get_transfer(conn: &Connection, id: i64) -> Result<Option<TransferRecord>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT id, peer_name, direction, source_path, dest_path, \
                bytes_transferred, files_count, duration_ms, status, \
                error_message, created_at \
         FROM file_transfers WHERE id = ?1",
    )?;
    let mut rows = stmt.query_map(rusqlite::params![id], map_row)?;
    match rows.next() {
        Some(Ok(rec)) => Ok(Some(rec)),
        Some(Err(e)) => Err(e),
        None => Ok(None),
    }
}

fn map_row(row: &rusqlite::Row<'_>) -> rusqlite::Result<TransferRecord> {
    Ok(TransferRecord {
        id: row.get(0)?,
        peer_name: row.get(1)?,
        direction: row.get(2)?,
        source_path: row.get(3)?,
        dest_path: row.get(4)?,
        bytes_transferred: row.get(5)?,
        files_count: row.get(6)?,
        duration_ms: row.get(7)?,
        status: row.get(8)?,
        error_message: row.get(9)?,
        created_at: row.get(10)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{TransferDirection, TransferStatus};

    fn setup_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    fn sample_req() -> TransferRequest {
        TransferRequest {
            source_path: "/data/project/".into(),
            dest_path: "/backup/project/".into(),
            peer_name: "studio-mac".into(),
            ssh_target: "rob@192.168.1.50".into(),
            direction: TransferDirection::Push,
            exclude_patterns: vec![],
        }
    }

    fn sample_result() -> TransferResult {
        TransferResult {
            peer_name: "studio-mac".into(),
            bytes_transferred: 4096,
            files_count: 12,
            duration_ms: 350,
            status: TransferStatus::Success,
        }
    }

    #[test]
    fn record_and_get_transfer() {
        let conn = setup_db();
        let id = record_transfer(&conn, &sample_result(), &sample_req()).unwrap();
        assert!(id > 0);
        let rec = get_transfer(&conn, id).unwrap().unwrap();
        assert_eq!(rec.peer_name, "studio-mac");
        assert_eq!(rec.bytes_transferred, 4096);
        assert_eq!(rec.status, "success");
    }

    #[test]
    fn list_transfers_all() {
        let conn = setup_db();
        record_transfer(&conn, &sample_result(), &sample_req()).unwrap();
        let list = list_transfers(&conn, None, 50).unwrap();
        assert_eq!(list.len(), 1);
    }

    #[test]
    fn list_transfers_by_peer() {
        let conn = setup_db();
        record_transfer(&conn, &sample_result(), &sample_req()).unwrap();
        let found = list_transfers(&conn, Some("studio-mac"), 50).unwrap();
        assert_eq!(found.len(), 1);
        let empty = list_transfers(&conn, Some("unknown-peer"), 50).unwrap();
        assert!(empty.is_empty());
    }

    #[test]
    fn get_transfer_not_found() {
        let conn = setup_db();
        let rec = get_transfer(&conn, 999).unwrap();
        assert!(rec.is_none());
    }

    #[test]
    fn record_failed_transfer() {
        let conn = setup_db();
        let mut res = sample_result();
        res.status = TransferStatus::Failed("connection refused".into());
        let id = record_transfer(&conn, &res, &sample_req()).unwrap();
        let rec = get_transfer(&conn, id).unwrap().unwrap();
        assert_eq!(rec.status, "failed");
        assert_eq!(rec.error_message.as_deref(), Some("connection refused"));
    }
}
