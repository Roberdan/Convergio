//! DB snapshot — atomic SQLite backup with WAL checkpoint.
//!
//! Creates a consistent copy of the database by issuing a WAL checkpoint
//! then performing an atomic file copy. Tracks snapshots in backup_snapshots.

use crate::types::{BackupError, BackupResult, SnapshotRecord};
use convergio_db::pool::ConnPool;
use rusqlite::params;
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use tracing::info;

/// Default backup directory under the data root.
pub fn backup_dir(data_root: &Path) -> PathBuf {
    data_root.join("backups")
}

/// Create an atomic snapshot of the SQLite database.
///
/// 1. Issue WAL checkpoint (TRUNCATE) for consistency
/// 2. Copy the database file atomically (via temp + rename)
/// 3. Compute SHA-256 checksum of the copy
/// 4. Record the snapshot in backup_snapshots table
pub fn create_snapshot(
    pool: &ConnPool,
    db_path: &Path,
    dest_dir: &Path,
    node: &str,
) -> BackupResult<SnapshotRecord> {
    std::fs::create_dir_all(dest_dir)?;

    // WAL checkpoint for consistency
    let conn = pool.get()?;
    conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE);")?;
    drop(conn);

    // Generate snapshot ID and paths
    let snap_id = format!("snap-{}", uuid::Uuid::new_v4());
    let timestamp = chrono::Utc::now().format("%Y%m%d-%H%M%S").to_string();
    let filename = format!("convergio-{timestamp}.db");
    let dest_path = dest_dir.join(&filename);
    let tmp_path = dest_dir.join(format!(".{filename}.tmp"));

    // Atomic copy: write to temp, then rename
    std::fs::copy(db_path, &tmp_path)?;
    std::fs::rename(&tmp_path, &dest_path)?;

    // Compute checksum
    let checksum = compute_file_checksum(&dest_path)?;
    let size_bytes = std::fs::metadata(&dest_path)?.len() as i64;

    let record = SnapshotRecord {
        id: snap_id,
        path: dest_path.to_string_lossy().into_owned(),
        size_bytes,
        checksum,
        created_at: chrono::Utc::now().to_rfc3339(),
        node: node.to_string(),
    };

    // Record in DB
    let conn = pool.get()?;
    conn.execute(
        "INSERT INTO backup_snapshots (id, path, size_bytes, checksum, node) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            record.id,
            record.path,
            record.size_bytes,
            record.checksum,
            record.node,
        ],
    )?;

    info!(
        snapshot = %record.id,
        size = record.size_bytes,
        path = %record.path,
        "snapshot created"
    );
    Ok(record)
}

/// List all recorded snapshots, newest first.
pub fn list_snapshots(pool: &ConnPool) -> BackupResult<Vec<SnapshotRecord>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT id, path, size_bytes, checksum, created_at, node \
         FROM backup_snapshots ORDER BY created_at DESC",
    )?;
    let records = stmt
        .query_map([], |row| {
            Ok(SnapshotRecord {
                id: row.get(0)?,
                path: row.get(1)?,
                size_bytes: row.get(2)?,
                checksum: row.get(3)?,
                created_at: row.get(4)?,
                node: row.get(5)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(records)
}

/// Find a snapshot by ID.
pub fn get_snapshot(pool: &ConnPool, snap_id: &str) -> BackupResult<SnapshotRecord> {
    let conn = pool.get()?;
    conn.query_row(
        "SELECT id, path, size_bytes, checksum, created_at, node \
         FROM backup_snapshots WHERE id = ?1",
        params![snap_id],
        |row| {
            Ok(SnapshotRecord {
                id: row.get(0)?,
                path: row.get(1)?,
                size_bytes: row.get(2)?,
                checksum: row.get(3)?,
                created_at: row.get(4)?,
                node: row.get(5)?,
            })
        },
    )
    .map_err(|_| BackupError::SnapshotNotFound(snap_id.to_string()))
}

/// Compute SHA-256 checksum of a file. Reads in 8 KiB chunks.
fn compute_file_checksum(path: &Path) -> BackupResult<String> {
    use std::io::Read;
    let mut file = std::fs::File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 8192];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// Verify a snapshot file matches its recorded checksum.
pub fn verify_snapshot(record: &SnapshotRecord) -> BackupResult<bool> {
    let path = Path::new(&record.path);
    if !path.exists() {
        return Err(BackupError::SnapshotNotFound(record.id.clone()));
    }
    let actual = compute_file_checksum(path)?;
    Ok(actual == record.checksum)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> (ConnPool, tempfile::TempDir) {
        let tmp = tempfile::tempdir().unwrap();
        let db_path = tmp.path().join("test.db");
        let pool = convergio_db::pool::create_pool(&db_path).unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute_batch("CREATE TABLE test_data (id INTEGER, val TEXT)")
            .unwrap();
        conn.execute("INSERT INTO test_data VALUES (1, 'hello')", [])
            .unwrap();
        drop(conn);
        (pool, tmp)
    }

    #[test]
    fn create_and_list_snapshot() {
        let (pool, tmp) = setup();
        let db_path = tmp.path().join("test.db");
        let dest = tmp.path().join("backups");
        let rec = create_snapshot(&pool, &db_path, &dest, "test-node").unwrap();
        assert!(rec.id.starts_with("snap-"));
        assert!(rec.size_bytes > 0);
        assert!(!rec.checksum.is_empty());

        let list = list_snapshots(&pool).unwrap();
        assert_eq!(list.len(), 1);
        assert_eq!(list[0].id, rec.id);
    }

    #[test]
    fn get_snapshot_by_id() {
        let (pool, tmp) = setup();
        let db_path = tmp.path().join("test.db");
        let dest = tmp.path().join("backups");
        let rec = create_snapshot(&pool, &db_path, &dest, "test-node").unwrap();
        let found = get_snapshot(&pool, &rec.id).unwrap();
        assert_eq!(found.checksum, rec.checksum);
    }

    #[test]
    fn verify_snapshot_integrity() {
        let (pool, tmp) = setup();
        let db_path = tmp.path().join("test.db");
        let dest = tmp.path().join("backups");
        let rec = create_snapshot(&pool, &db_path, &dest, "test-node").unwrap();
        assert!(verify_snapshot(&rec).unwrap());
    }

    #[test]
    fn snapshot_not_found_error() {
        let (pool, _tmp) = setup();
        let result = get_snapshot(&pool, "snap-nonexistent");
        assert!(result.is_err());
    }
}
