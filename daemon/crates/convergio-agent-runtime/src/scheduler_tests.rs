//! Tests for scheduler module.

use super::*;
use crate::schema;
use crate::types::SpawnRequest;

fn setup() -> rusqlite::Connection {
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    for m in schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn
}

fn req(name: &str, org: &str, priority: i32) -> SpawnRequest {
    SpawnRequest {
        agent_name: name.into(),
        org_id: org.into(),
        task_id: None,
        capabilities: vec![],
        model_preference: None,
        budget_usd: 10.0,
        priority,
    }
}

#[test]
fn enqueue_and_dequeue_by_priority() {
    let conn = setup();
    enqueue(&conn, &req("low", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("high", "org-a", 10), None).unwrap();
    enqueue(&conn, &req("mid", "org-a", 5), None).unwrap();

    let (_, r1) = dequeue(&conn).unwrap().unwrap();
    assert_eq!(r1.agent_name, "high");
    let (_, r2) = dequeue(&conn).unwrap().unwrap();
    assert_eq!(r2.agent_name, "mid");
    let (_, r3) = dequeue(&conn).unwrap().unwrap();
    assert_eq!(r3.agent_name, "low");
    assert!(dequeue(&conn).unwrap().is_none());
}

#[test]
fn backpressure_rejects_when_full() {
    let conn = setup();
    let r = req("agent", "org-a", 1);
    for _ in 0..3 {
        enqueue(&conn, &r, Some(3)).unwrap();
    }
    let err = enqueue(&conn, &r, Some(3)).unwrap_err();
    assert!(err.to_string().contains("queue full"));
}

#[test]
fn queue_depth_counts_correctly() {
    let conn = setup();
    enqueue(&conn, &req("a", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("b", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("c", "org-b", 1), None).unwrap();

    assert_eq!(queue_depth_for_org(&conn, "org-a").unwrap(), 2);
    assert_eq!(queue_depth_for_org(&conn, "org-b").unwrap(), 1);
    assert_eq!(queue_depth_total(&conn).unwrap(), 3);
}

#[test]
fn drain_org_removes_all_entries() {
    let conn = setup();
    enqueue(&conn, &req("a", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("b", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("c", "org-b", 1), None).unwrap();

    let drained = drain_org(&conn, "org-a").unwrap();
    assert_eq!(drained, 2);
    assert_eq!(queue_depth_total(&conn).unwrap(), 1);
}

#[test]
fn list_pending_returns_ordered() {
    let conn = setup();
    enqueue(&conn, &req("low", "org-a", 1), None).unwrap();
    enqueue(&conn, &req("high", "org-a", 10), None).unwrap();

    let pending = list_pending(&conn).unwrap();
    assert_eq!(pending.len(), 2);
    assert_eq!(pending[0].priority, 10);
    assert_eq!(pending[1].priority, 1);
}
