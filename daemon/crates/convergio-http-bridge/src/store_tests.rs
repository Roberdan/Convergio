//! Tests for the http-bridge store module.

use super::*;
use crate::schema;
use convergio_db::pool::create_memory_pool;
use convergio_types::manifest::{Manifest, ModuleKind};

fn setup() -> r2d2::PooledConnection<r2d2_sqlite::SqliteConnectionManager> {
    let pool = create_memory_pool().unwrap();
    let conn = pool.get().unwrap();
    for m in schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn
}

fn sample_request(id: &str) -> RegisterRequest {
    RegisterRequest {
        id: id.to_string(),
        manifest: Manifest {
            id: id.to_string(),
            description: "Test external extension".to_string(),
            version: "1.0.0".to_string(),
            kind: ModuleKind::Integration,
            provides: vec![],
            requires: vec![],
            agent_tools: vec![],
        },
        base_url: "http://localhost:3100".to_string(),
        health_endpoint: "/health".to_string(),
        events_webhook: "/webhook/events".to_string(),
        routes_prefix: format!("/api/ext/{id}"),
    }
}

#[test]
fn insert_and_get() {
    let conn = setup();
    let req = sample_request("ext-alpha");
    insert_extension(&conn, &req).unwrap();
    let ext = get_by_id(&conn, "ext-alpha").unwrap().unwrap();
    assert_eq!(ext.id, "ext-alpha");
    assert_eq!(ext.state, BridgeState::Registered);
    assert_eq!(ext.base_url, "http://localhost:3100");
    assert_eq!(ext.consecutive_failures, 0);
}

#[test]
fn list_excludes_removed() {
    let conn = setup();
    insert_extension(&conn, &sample_request("ext-a")).unwrap();
    insert_extension(&conn, &sample_request("ext-b")).unwrap();
    remove_extension(&conn, "ext-b").unwrap();
    let active = list_active(&conn).unwrap();
    assert_eq!(active.len(), 1);
    assert_eq!(active[0].id, "ext-a");
}

#[test]
fn update_health_transitions() {
    let conn = setup();
    insert_extension(&conn, &sample_request("ext-hc")).unwrap();
    update_health(&conn, "ext-hc", BridgeState::Active, 0).unwrap();
    let ext = get_by_id(&conn, "ext-hc").unwrap().unwrap();
    assert_eq!(ext.state, BridgeState::Active);
    assert!(ext.last_health_check.is_some());

    update_health(&conn, "ext-hc", BridgeState::Degraded, 3).unwrap();
    let ext = get_by_id(&conn, "ext-hc").unwrap().unwrap();
    assert_eq!(ext.state, BridgeState::Degraded);
    assert_eq!(ext.consecutive_failures, 3);
}

#[test]
fn duplicate_insert_fails() {
    let conn = setup();
    insert_extension(&conn, &sample_request("ext-dup")).unwrap();
    let result = insert_extension(&conn, &sample_request("ext-dup"));
    assert!(result.is_err());
}

#[test]
fn remove_nonexistent_returns_false() {
    let conn = setup();
    let removed = remove_extension(&conn, "no-such-ext").unwrap();
    assert!(!removed);
}
