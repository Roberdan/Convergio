//! Disaster recovery — restore daemon from a snapshot.
//!
//! Validates the snapshot checksum before replacing the live database.
//! The restore is atomic: copy to temp, verify, then rename.

use crate::snapshot::{get_snapshot, verify_snapshot};
use crate::types::{BackupError, BackupResult};
use convergio_db::pool::ConnPool;
use std::path::Path;
use tracing::{info, warn};

/// Restore the database from a snapshot file.
///
/// 1. Find the snapshot record by ID
/// 2. Verify the snapshot file checksum
/// 3. Copy snapshot to temp location next to target
/// 4. Rename temp over the live database (atomic on same filesystem)
///
/// The caller must stop the daemon or close all pool connections
/// before calling this. Returns the path of the restored file.
pub fn restore_from_snapshot(
    pool: &ConnPool,
    snap_id: &str,
    target_db_path: &Path,
) -> BackupResult<String> {
    let record = get_snapshot(pool, snap_id)?;

    let snap_path = Path::new(&record.path);
    if !snap_path.exists() {
        return Err(BackupError::SnapshotNotFound(format!(
            "file missing: {}",
            record.path
        )));
    }

    // Verify integrity
    if !verify_snapshot(&record)? {
        return Err(BackupError::RestoreFailed(
            "checksum mismatch — snapshot may be corrupted".into(),
        ));
    }

    info!(snapshot = %snap_id, "verified snapshot integrity, starting restore");

    // Atomic restore: copy to temp, then rename
    let tmp_path = target_db_path.with_extension("db.restoring");
    std::fs::copy(snap_path, &tmp_path)?;

    // Remove WAL and SHM files from target (stale after restore)
    let wal = target_db_path.with_extension("db-wal");
    let shm = target_db_path.with_extension("db-shm");
    remove_if_exists(&wal);
    remove_if_exists(&shm);

    // Rename temp over live DB
    std::fs::rename(&tmp_path, target_db_path)?;

    info!(
        snapshot = %snap_id,
        target = %target_db_path.display(),
        "database restored from snapshot"
    );
    Ok(record.path)
}

/// Restore from a raw snapshot file path (no pool lookup).
/// Used by `cvg backup restore <file>` when the DB may not be running.
pub fn restore_from_file(snapshot_path: &Path, target_db_path: &Path) -> BackupResult<()> {
    if !snapshot_path.exists() {
        return Err(BackupError::SnapshotNotFound(
            snapshot_path.to_string_lossy().into_owned(),
        ));
    }

    let tmp_path = target_db_path.with_extension("db.restoring");
    std::fs::copy(snapshot_path, &tmp_path)?;

    // Remove stale WAL/SHM
    remove_if_exists(&target_db_path.with_extension("db-wal"));
    remove_if_exists(&target_db_path.with_extension("db-shm"));

    std::fs::rename(&tmp_path, target_db_path)?;

    info!(
        source = %snapshot_path.display(),
        target = %target_db_path.display(),
        "database restored from file"
    );
    Ok(())
}

fn remove_if_exists(path: &Path) {
    if path.exists() {
        if let Err(e) = std::fs::remove_file(path) {
            warn!(path = %path.display(), err = %e, "failed to remove stale file");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn restore_from_file_copies_correctly() {
        let tmp = tempfile::tempdir().unwrap();
        let source = tmp.path().join("source.db");
        let target = tmp.path().join("target.db");
        std::fs::write(&source, b"fake-sqlite-data").unwrap();

        restore_from_file(&source, &target).unwrap();

        assert!(target.exists());
        let content = std::fs::read(&target).unwrap();
        assert_eq!(content, b"fake-sqlite-data");
    }

    #[test]
    fn restore_from_file_removes_stale_wal() {
        let tmp = tempfile::tempdir().unwrap();
        let source = tmp.path().join("source.db");
        let target = tmp.path().join("target.db");
        let wal = tmp.path().join("target.db-wal");
        let shm = tmp.path().join("target.db-shm");

        std::fs::write(&source, b"db-data").unwrap();
        std::fs::write(&wal, b"stale-wal").unwrap();
        std::fs::write(&shm, b"stale-shm").unwrap();

        restore_from_file(&source, &target).unwrap();

        assert!(!wal.exists());
        assert!(!shm.exists());
    }

    #[test]
    fn restore_from_missing_file_errors() {
        let tmp = tempfile::tempdir().unwrap();
        let result = restore_from_file(
            &tmp.path().join("nonexistent.db"),
            &tmp.path().join("target.db"),
        );
        assert!(result.is_err());
    }

    #[test]
    fn restore_from_snapshot_round_trip() {
        let tmp = tempfile::tempdir().unwrap();
        let db_path = tmp.path().join("live.db");
        let pool = convergio_db::pool::create_pool(&db_path).unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn.execute_batch("CREATE TABLE test_rt (v TEXT)").unwrap();
        conn.execute("INSERT INTO test_rt VALUES ('original')", [])
            .unwrap();
        drop(conn);

        // Create snapshot
        let dest = tmp.path().join("backups");
        let rec = crate::snapshot::create_snapshot(&pool, &db_path, &dest, "test-node").unwrap();

        // Modify live DB
        let conn = pool.get().unwrap();
        conn.execute("DELETE FROM test_rt", []).unwrap();
        drop(conn);

        // Restore
        let snap_path = std::path::Path::new(&rec.path);
        restore_from_file(snap_path, &db_path).unwrap();

        // Verify restoration
        let conn2 = rusqlite::Connection::open(&db_path).unwrap();
        let val: String = conn2
            .query_row("SELECT v FROM test_rt", [], |r| r.get(0))
            .unwrap();
        assert_eq!(val, "original");
    }
}
