// Human-in-the-loop formal approval gates with thresholds.
// WHY: Critical operations (budget exceed, deploy, wave advance) need
// explicit human sign-off before proceeding.

use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovalRequest {
    pub id: i64,
    pub plan_id: i64,
    pub task_id: Option<i64>,
    pub approval_type: String,
    pub requester: String,
    pub reason: String,
    pub status: String,
    pub reviewer: Option<String>,
    pub review_comment: Option<String>,
    pub reviewed_at: Option<String>,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovalThreshold {
    pub id: i64,
    pub trigger_type: String,
    pub threshold_value: f64,
    pub require_approval: bool,
    pub auto_approve_below: f64,
}

/// Create a new approval request. Returns the new row id.
pub fn create_approval(
    conn: &Connection,
    plan_id: i64,
    task_id: Option<i64>,
    approval_type: &str,
    requester: &str,
    reason: &str,
) -> rusqlite::Result<i64> {
    conn.execute(
        "INSERT INTO approval_requests \
         (plan_id, task_id, approval_type, requester, reason) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![plan_id, task_id, approval_type, requester, reason],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Mark an approval request as approved.
pub fn approve(conn: &Connection, id: i64, reviewer: &str) -> rusqlite::Result<()> {
    let n = conn.execute(
        "UPDATE approval_requests SET status='approved', \
         reviewer=?1, reviewed_at=datetime('now') WHERE id=?2 \
         AND status='pending'",
        params![reviewer, id],
    )?;
    if n == 0 {
        return Err(rusqlite::Error::QueryReturnedNoRows);
    }
    Ok(())
}

/// Mark an approval request as rejected.
pub fn reject(conn: &Connection, id: i64, reviewer: &str, comment: &str) -> rusqlite::Result<()> {
    let n = conn.execute(
        "UPDATE approval_requests SET status='rejected', \
         reviewer=?1, review_comment=?2, reviewed_at=datetime('now') \
         WHERE id=?3 AND status='pending'",
        params![reviewer, comment, id],
    )?;
    if n == 0 {
        return Err(rusqlite::Error::QueryReturnedNoRows);
    }
    Ok(())
}

/// List all pending approval requests.
pub fn list_pending(conn: &Connection) -> Vec<ApprovalRequest> {
    let mut stmt = match conn.prepare(
        "SELECT id, plan_id, task_id, approval_type, requester, \
         reason, status, reviewer, review_comment, reviewed_at, \
         created_at FROM approval_requests WHERE status='pending' \
         ORDER BY created_at ASC",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    stmt.query_map([], |r| Ok(row_to_approval(r)))
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

/// Get a single approval request by id.
pub fn get_approval(conn: &Connection, id: i64) -> Option<ApprovalRequest> {
    conn.query_row(
        "SELECT id, plan_id, task_id, approval_type, requester, \
         reason, status, reviewer, review_comment, reviewed_at, \
         created_at FROM approval_requests WHERE id=?1",
        [id],
        |r| Ok(row_to_approval(r)),
    )
    .ok()
}

fn row_to_approval(r: &rusqlite::Row) -> ApprovalRequest {
    ApprovalRequest {
        id: r.get(0).unwrap_or(0),
        plan_id: r.get(1).unwrap_or(0),
        task_id: r.get(2).unwrap_or(None),
        approval_type: r.get(3).unwrap_or_default(),
        requester: r.get(4).unwrap_or_default(),
        reason: r.get(5).unwrap_or_default(),
        status: r.get(6).unwrap_or_default(),
        reviewer: r.get(7).unwrap_or(None),
        review_comment: r.get(8).unwrap_or(None),
        reviewed_at: r.get(9).unwrap_or(None),
        created_at: r.get(10).unwrap_or_default(),
    }
}

/// Check whether a given trigger+value requires human approval.
/// Returns `true` if approval is needed.
pub fn check_threshold(conn: &Connection, trigger: &str, value: f64) -> bool {
    conn.query_row(
        "SELECT require_approval, threshold_value, auto_approve_below \
         FROM approval_thresholds WHERE trigger_type=?1",
        [trigger],
        |r| {
            let require: bool = r.get(0)?;
            let threshold: f64 = r.get(1)?;
            let auto_below: f64 = r.get(2)?;
            Ok((require, threshold, auto_below))
        },
    )
    .map(|(require, _threshold, auto_below)| {
        if !require {
            return false;
        }
        if value < auto_below {
            return false;
        }
        // Value is at or above auto-approve floor — needs human sign-off
        true
    })
    .unwrap_or(false)
}

/// Set or update a threshold for a trigger type.
pub fn set_threshold(
    conn: &Connection,
    trigger: &str,
    threshold: f64,
    auto_approve_below: f64,
) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO approval_thresholds \
         (trigger_type, threshold_value, require_approval, auto_approve_below) \
         VALUES (?1, ?2, 1, ?3) \
         ON CONFLICT(trigger_type) DO UPDATE SET \
         threshold_value=excluded.threshold_value, \
         auto_approve_below=excluded.auto_approve_below, \
         require_approval=1",
        params![trigger, threshold, auto_approve_below],
    )?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        for m in crate::schema_tracking::tracking_migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn test_create_and_approve() {
        let conn = setup();
        let id = create_approval(&conn, 1, None, "deploy", "alice", "production release").unwrap();
        assert!(id > 0);
        let req = get_approval(&conn, id).unwrap();
        assert_eq!(req.status, "pending");

        approve(&conn, id, "bob").unwrap();
        let req = get_approval(&conn, id).unwrap();
        assert_eq!(req.status, "approved");
        assert_eq!(req.reviewer.as_deref(), Some("bob"));
    }

    #[test]
    fn test_create_and_reject() {
        let conn = setup();
        let id =
            create_approval(&conn, 2, Some(5), "budget_exceed", "carol", "over limit").unwrap();
        reject(&conn, id, "dave", "too expensive").unwrap();
        let req = get_approval(&conn, id).unwrap();
        assert_eq!(req.status, "rejected");
        assert_eq!(req.review_comment.as_deref(), Some("too expensive"));
    }

    #[test]
    fn test_list_pending() {
        let conn = setup();
        create_approval(&conn, 1, None, "deploy", "a", "r1").unwrap();
        create_approval(&conn, 1, None, "wave", "b", "r2").unwrap();
        let id3 = create_approval(&conn, 1, None, "budget", "c", "r3").unwrap();
        approve(&conn, id3, "d").unwrap();

        let pending = list_pending(&conn);
        assert_eq!(pending.len(), 2);
    }

    #[test]
    fn test_threshold_check() {
        let conn = setup();
        // No threshold set — should return false
        assert!(!check_threshold(&conn, "budget_exceed", 100.0));

        // Set threshold: require approval >= 50, auto-approve below 10
        set_threshold(&conn, "budget_exceed", 50.0, 10.0).unwrap();

        assert!(!check_threshold(&conn, "budget_exceed", 5.0));
        assert!(check_threshold(&conn, "budget_exceed", 50.0));
        assert!(check_threshold(&conn, "budget_exceed", 75.0));
        // Between auto_approve_below and threshold — needs approval
        assert!(check_threshold(&conn, "budget_exceed", 25.0));
    }
}
