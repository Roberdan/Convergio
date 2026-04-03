//! Tests for delegation chain module.

use super::*;
use rusqlite::Connection;

fn setup() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    for m in crate::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    // Insert root execution
    conn.execute(
        "INSERT INTO lr_executions (id, agent, node, budget_usd, stage) \
         VALUES ('root', 'elena', 'M5Max', 10.0, 'running')",
        [],
    )
    .unwrap();
    conn
}

#[test]
fn create_and_list_children() {
    let conn = setup();
    create_child(&conn, "child-1", "root", "baccio", "M1Pro", 3.0, None).unwrap();
    create_child(
        &conn,
        "child-2",
        "root",
        "marco",
        "M5Max",
        2.0,
        Some("2026-04-10T00:00:00Z"),
    )
    .unwrap();
    let children = list_children(&conn, "root").unwrap();
    assert_eq!(children.len(), 2);
    assert_eq!(children[0].agent, "baccio");
    assert_eq!(
        children[1].deadline.as_deref(),
        Some("2026-04-10T00:00:00Z")
    );
}

#[test]
fn build_tree_nested() {
    let conn = setup();
    create_child(&conn, "mid", "root", "baccio", "M1Pro", 5.0, None).unwrap();
    create_child(&conn, "leaf", "mid", "marco", "M5Max", 2.0, None).unwrap();
    let tree = build_tree(&conn, "root").unwrap().unwrap();
    assert_eq!(tree.execution_id, "root");
    assert_eq!(tree.children.len(), 1);
    assert_eq!(tree.children[0].execution_id, "mid");
    assert_eq!(tree.children[0].children.len(), 1);
    assert_eq!(tree.children[0].children[0].execution_id, "leaf");
}

#[test]
fn build_tree_missing_returns_none() {
    let conn = setup();
    assert!(build_tree(&conn, "nonexistent").unwrap().is_none());
}

#[test]
fn cascade_death_kills_descendants() {
    let conn = setup();
    create_child(&conn, "mid", "root", "b", "n", 0.0, None).unwrap();
    create_child(&conn, "leaf", "mid", "c", "n", 0.0, None).unwrap();
    // Mark both as running
    conn.execute(
        "UPDATE lr_executions SET stage = 'running' WHERE id IN ('mid', 'leaf')",
        [],
    )
    .unwrap();
    let reaped = cascade_death(&conn, "root").unwrap();
    assert_eq!(reaped, 2);
    let stage: String = conn
        .query_row(
            "SELECT stage FROM lr_executions WHERE id = 'leaf'",
            [],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(stage, "reaped");
}

#[test]
fn cascade_death_skips_terminal() {
    let conn = setup();
    create_child(&conn, "done-child", "root", "b", "n", 0.0, None).unwrap();
    conn.execute(
        "UPDATE lr_executions SET stage = 'completing' WHERE id = 'done-child'",
        [],
    )
    .unwrap();
    let reaped = cascade_death(&conn, "root").unwrap();
    assert_eq!(reaped, 0);
}
