// Rollback — captures pre-task snapshots and restores them on demand.

use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::path::Path;
use std::process::Command;

type RollbackResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// Capture current git HEAD, changed files, and the task DB row as a snapshot.
pub fn save_snapshot(conn: &Connection, task_id: i64, worktree_path: &Path) -> RollbackResult<i64> {
    let git_ref = git_rev_parse(worktree_path)?;
    let changed_files = git_changed_files(worktree_path)?;

    let db_rows_json: Option<String> = conn
        .query_row(
            "SELECT id, task_id, title, status, description FROM tasks WHERE id = ?1",
            params![task_id],
            |row| {
                Ok(json!({
                    "id":          row.get::<_, i64>(0)?,
                    "task_id":     row.get::<_, Option<String>>(1)?,
                    "title":       row.get::<_, Option<String>>(2)?,
                    "status":      row.get::<_, Option<String>>(3)?,
                    "description": row.get::<_, Option<String>>(4)?,
                })
                .to_string())
            },
        )
        .ok();

    conn.execute(
        "INSERT INTO rollback_snapshots (task_id, git_ref, changed_files, db_rows_json)
         VALUES (?1, ?2, ?3, ?4)",
        params![task_id, git_ref, changed_files, db_rows_json],
    )?;

    Ok(conn.last_insert_rowid())
}

/// Restore the latest snapshot: checks out saved git_ref, resets task to pending.
pub fn restore_snapshot(
    conn: &Connection,
    task_id: i64,
    worktree_path: &Path,
) -> RollbackResult<()> {
    let git_ref: String = conn
        .query_row(
            "SELECT git_ref FROM rollback_snapshots WHERE task_id = ?1 ORDER BY id DESC LIMIT 1",
            params![task_id],
            |row| row.get(0),
        )
        .map_err(|_| format!("no snapshot found for task {task_id}"))?;

    let out = Command::new("git")
        .args(["checkout", &git_ref])
        .current_dir(worktree_path)
        .output()
        .map_err(|e| format!("git checkout failed: {e}"))?;

    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr);
        return Err(format!("git checkout {git_ref} failed: {stderr}").into());
    }

    conn.execute(
        "UPDATE tasks SET status = 'pending', started_at = NULL WHERE id = ?1",
        params![task_id],
    )?;
    Ok(())
}

/// Return all snapshots for a task, newest first.
pub fn list_snapshots(conn: &Connection, task_id: i64) -> rusqlite::Result<Vec<Value>> {
    let mut stmt = conn.prepare(
        "SELECT id, task_id, git_ref, changed_files, db_rows_json, created_at
         FROM rollback_snapshots WHERE task_id = ?1 ORDER BY id DESC",
    )?;
    let rows: rusqlite::Result<Vec<Value>> = stmt
        .query_map(params![task_id], |row| {
            Ok(json!({
                "id":            row.get::<_, i64>(0)?,
                "task_id":       row.get::<_, Option<i64>>(1)?,
                "git_ref":       row.get::<_, String>(2)?,
                "changed_files": row.get::<_, Option<String>>(3)?,
                "db_rows_json":  row.get::<_, Option<String>>(4)?,
                "created_at":    row.get::<_, Option<String>>(5)?,
            }))
        })?
        .collect();
    rows
}

fn git_rev_parse(worktree_path: &Path) -> RollbackResult<String> {
    let out = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(worktree_path)
        .output()
        .map_err(|e| format!("git rev-parse failed: {e}"))?;
    if !out.status.success() {
        return Err(format!("git rev-parse HEAD failed in {:?}", worktree_path).into());
    }
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

fn git_changed_files(worktree_path: &Path) -> RollbackResult<Option<String>> {
    let out = Command::new("git")
        .args(["diff", "--name-only", "HEAD"])
        .current_dir(worktree_path)
        .output()
        .map_err(|e| format!("git diff failed: {e}"))?;
    let text = String::from_utf8_lossy(&out.stdout).trim().to_string();
    Ok(if text.is_empty() { None } else { Some(text) })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        conn.execute_batch("PRAGMA foreign_keys = OFF;").unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn list_snapshots_empty() {
        let conn = setup();
        assert!(list_snapshots(&conn, 999).unwrap().is_empty());
    }

    #[test]
    fn restore_no_snapshot_errors() {
        let conn = setup();
        let err = restore_snapshot(&conn, 42, Path::new("/nonexistent")).unwrap_err();
        assert!(err.to_string().contains("no snapshot found"));
    }

    #[test]
    fn save_and_list_snapshot() {
        let conn = setup();
        conn.execute(
            "INSERT INTO plans (id, project_id, name) VALUES (1, 'p1', 'test')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO tasks (id, plan_id, task_id, title, status) VALUES (1, 1, 'T1', 'Test', 'in_progress')",
            [],
        ).unwrap();
        conn.execute(
            "INSERT INTO rollback_snapshots (task_id, git_ref, changed_files) VALUES (?1, ?2, ?3)",
            params![1i64, "deadbeef", "src/lib.rs"],
        )
        .unwrap();
        let snaps = list_snapshots(&conn, 1).unwrap();
        assert_eq!(snaps.len(), 1);
        assert_eq!(snaps[0]["git_ref"], "deadbeef");
    }
}
