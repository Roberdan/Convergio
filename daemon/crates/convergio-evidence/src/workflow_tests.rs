use super::*;

fn setup() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    for m in convergio_orchestrator::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    for m in crate::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn.execute(
        "INSERT INTO plans(id, project_id, name) VALUES (1, 'p', 'plan')",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO waves(id, wave_id, plan_id, status) \
         VALUES (1, 'w1', 1, 'active')",
        [],
    )
    .unwrap();
    conn
}

#[test]
fn wave_completion_triggers_when_all_done() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) VALUES (1, 1, 1, 'done')",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) VALUES (2, 1, 1, 'done')",
        [],
    )
    .unwrap();
    let completed = check_wave_completion(&conn, 1).unwrap();
    assert!(completed);
    let count: i64 = conn
        .query_row("SELECT COUNT(*) FROM validation_queue", [], |r| r.get(0))
        .unwrap();
    assert_eq!(count, 1);
}

#[test]
fn wave_not_complete_with_pending_tasks() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) VALUES (1, 1, 1, 'done')",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) \
         VALUES (2, 1, 1, 'in_progress')",
        [],
    )
    .unwrap();
    assert!(!check_wave_completion(&conn, 1).unwrap());
}

#[test]
fn stale_detection_records_notification() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status, started_at) \
         VALUES (1, 1, 1, 'in_progress', datetime('now', '-120 minutes'))",
        [],
    )
    .unwrap();
    let stale = detect_stale_tasks(&conn, 60).unwrap();
    assert_eq!(stale.len(), 1);
    let stale2 = detect_stale_tasks(&conn, 60).unwrap();
    assert!(stale2.is_empty());
}

#[test]
fn resolve_stale_allows_re_detection() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status, started_at) \
         VALUES (1, 1, 1, 'in_progress', datetime('now', '-120 minutes'))",
        [],
    )
    .unwrap();
    detect_stale_tasks(&conn, 60).unwrap();
    resolve_stale_notification(&conn, 1);
    let stale = detect_stale_tasks(&conn, 60).unwrap();
    assert_eq!(stale.len(), 1);
}

#[test]
fn commit_matching_extracts_task_refs() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) VALUES (1, 1, 1, 'pending')",
        [],
    )
    .unwrap();
    let matched = match_commit_to_task(&conn, "abc123", "feat: implement task-1 feature");
    assert_eq!(matched, vec![1]);
    assert!(crate::evidence::has_evidence(&conn, 1, "commit_hash"));
}

#[test]
fn commit_matching_hash_ref() {
    let conn = setup();
    conn.execute(
        "INSERT INTO tasks(id, plan_id, wave_id, status) VALUES (1, 1, 1, 'pending')",
        [],
    )
    .unwrap();
    let matched = match_commit_to_task(&conn, "def456", "fix: resolve #1 bug");
    assert_eq!(matched, vec![1]);
}

#[test]
fn commit_matching_ignores_nonexistent() {
    let conn = setup();
    let matched = match_commit_to_task(&conn, "abc", "feat: task-999");
    assert!(matched.is_empty());
}
