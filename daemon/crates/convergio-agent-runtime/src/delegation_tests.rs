//! Tests for delegation module.

use super::*;
use crate::schema;

fn setup() -> rusqlite::Connection {
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    for m in schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    // Two running agents in different orgs
    conn.execute(
        "INSERT INTO art_agents (id, agent_name, org_id, node, stage) \
         VALUES ('a1', 'elena', 'legal-corp', 'n1', 'running')",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO art_agents (id, agent_name, org_id, node, stage) \
         VALUES ('a2', 'baccio', 'dev-corp', 'n1', 'running')",
        [],
    )
    .unwrap();
    conn
}

#[test]
fn borrow_and_return() {
    let conn = setup();
    let did = borrow_agent(&conn, "a1", "dev-corp", Some(10), 5.0, 3600).unwrap();
    assert!(!did.is_empty());

    // Agent should be borrowed
    let stage: String = conn
        .query_row("SELECT stage FROM art_agents WHERE id = 'a1'", [], |r| {
            r.get(0)
        })
        .unwrap();
    assert_eq!(stage, "borrowed");

    return_agent(&conn, &did).unwrap();
    let stage: String = conn
        .query_row("SELECT stage FROM art_agents WHERE id = 'a1'", [], |r| {
            r.get(0)
        })
        .unwrap();
    assert_eq!(stage, "running");
}

#[test]
fn borrow_stopped_agent_fails() {
    let conn = setup();
    conn.execute(
        "UPDATE art_agents SET stage = 'stopped' WHERE id = 'a1'",
        [],
    )
    .unwrap();
    let err = borrow_agent(&conn, "a1", "dev-corp", None, 5.0, 3600).unwrap_err();
    assert!(err.to_string().contains("not running"));
}

#[test]
fn circular_delegation_detected() {
    let conn = setup();
    // Borrow a1 (legal-corp) to dev-corp
    borrow_agent(&conn, "a1", "dev-corp", None, 5.0, 3600).unwrap();
    // Now try to borrow a2 (dev-corp) to legal-corp — should detect cycle
    let err = borrow_agent(&conn, "a2", "legal-corp", None, 5.0, 3600).unwrap_err();
    assert!(err.to_string().contains("deadlock"));
}

#[test]
fn find_expired_empty_when_fresh() {
    let conn = setup();
    borrow_agent(&conn, "a1", "dev-corp", None, 5.0, 3600).unwrap();
    let expired = find_expired(&conn).unwrap();
    assert!(expired.is_empty());
}
