//! Tests for allocator module.

use super::*;
use crate::schema;

fn setup() -> rusqlite::Connection {
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    for m in schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn
}

fn sample_request() -> SpawnRequest {
    SpawnRequest {
        agent_name: "elena".into(),
        org_id: "legal-corp".into(),
        task_id: Some(42),
        capabilities: vec!["legal-review".into()],
        model_preference: Some("claude-opus-4".into()),
        budget_usd: 10.0,
        priority: 5,
    }
}

#[test]
fn spawn_creates_agent() {
    let conn = setup();
    let id = spawn(&conn, &sample_request(), "m5-max").unwrap();
    assert!(!id.is_empty());

    let agent = get(&conn, &id).unwrap();
    assert_eq!(agent.agent_name, "elena");
    assert_eq!(agent.org_id, "legal-corp");
    assert_eq!(agent.stage, AgentStage::Spawning);
    assert_eq!(agent.node, "m5-max");
}

#[test]
fn activate_transitions_to_running() {
    let conn = setup();
    let id = spawn(&conn, &sample_request(), "m5-max").unwrap();
    activate(&conn, &id).unwrap();

    let agent = get(&conn, &id).unwrap();
    assert_eq!(agent.stage, AgentStage::Running);
}

#[test]
fn activate_fails_if_not_spawning() {
    let conn = setup();
    let id = spawn(&conn, &sample_request(), "m5-max").unwrap();
    activate(&conn, &id).unwrap();
    // Second activate should fail — already running
    let err = activate(&conn, &id).unwrap_err();
    assert!(err.to_string().contains("not in spawning stage"));
}

#[test]
fn stop_org_stops_all_agents() {
    let conn = setup();
    let id1 = spawn(&conn, &sample_request(), "m5-max").unwrap();
    activate(&conn, &id1).unwrap();
    let mut req2 = sample_request();
    req2.agent_name = "baccio".into();
    let id2 = spawn(&conn, &req2, "m5-max").unwrap();
    activate(&conn, &id2).unwrap();

    let stopped = stop_org(&conn, "legal-corp").unwrap();
    assert_eq!(stopped, 2);

    let a1 = get(&conn, &id1).unwrap();
    assert_eq!(a1.stage, AgentStage::Stopped);
}

#[test]
fn list_active_filters_by_org() {
    let conn = setup();
    spawn(&conn, &sample_request(), "m5-max").unwrap();
    let mut req2 = sample_request();
    req2.org_id = "dev-corp".into();
    spawn(&conn, &req2, "m5-max").unwrap();

    let legal = list_active(&conn, Some("legal-corp")).unwrap();
    assert_eq!(legal.len(), 1);
    let all = list_active(&conn, None).unwrap();
    assert_eq!(all.len(), 2);
}

#[test]
fn get_nonexistent_returns_not_found() {
    let conn = setup();
    let err = get(&conn, "nonexistent").unwrap_err();
    assert!(err.to_string().contains("nonexistent"));
}
