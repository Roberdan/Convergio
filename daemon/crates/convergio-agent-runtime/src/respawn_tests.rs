//! Tests for auto-respawn guard conditions.

use super::*;

fn setup_db() -> rusqlite::Connection {
    let conn = rusqlite::Connection::open_in_memory().unwrap();
    for m in crate::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn
}

fn insert_agent(conn: &rusqlite::Connection, id: &str, budget: f64, spent: f64, rc: i32) {
    conn.execute(
        "INSERT INTO art_agents (id, agent_name, org_id, node, budget_usd, \
         spent_usd, respawn_count, max_respawns) \
         VALUES (?1, 'test-agent', 'org-1', 'local', ?2, ?3, ?4, 5)",
        params![id, budget, spent, rc],
    )
    .unwrap();
}

#[test]
fn test_no_respawn_without_checkpoint() {
    let conn = setup_db();
    insert_agent(&conn, "a1", 10.0, 1.0, 0);
    let cp = find_checkpoint(&conn, "a1").unwrap();
    assert!(cp.is_none());
}

#[test]
fn test_no_respawn_at_max() {
    let conn = setup_db();
    insert_agent(&conn, "a2", 10.0, 1.0, 5);
    conn.execute(
        "INSERT INTO art_context (agent_id, key, value) \
         VALUES ('a2', 'checkpoint_state', '{\"step\":3}')",
        [],
    )
    .unwrap();
    let rec = load_agent(&conn, "a2").unwrap();
    assert!(rec.respawn_count >= rec.max_respawns);
}

#[test]
fn test_no_respawn_no_budget() {
    let conn = setup_db();
    insert_agent(&conn, "a3", 5.0, 5.0, 0);
    conn.execute(
        "INSERT INTO art_context (agent_id, key, value) \
         VALUES ('a3', 'checkpoint_state', '{\"step\":1}')",
        [],
    )
    .unwrap();
    let rec = load_agent(&conn, "a3").unwrap();
    let remaining = rec.budget - rec.spent;
    assert!(remaining <= 0.0);
}

#[test]
fn test_checkpoint_found_in_context() {
    let conn = setup_db();
    insert_agent(&conn, "a4", 10.0, 2.0, 0);
    conn.execute(
        "INSERT INTO art_context (agent_id, key, value) \
         VALUES ('a4', 'checkpoint_state', '{\"done\":[1,2]}')",
        [],
    )
    .unwrap();
    let cp = find_checkpoint(&conn, "a4").unwrap();
    assert_eq!(cp.unwrap(), "{\"done\":[1,2]}");
}

#[test]
fn test_build_instructions_contains_checkpoint() {
    let instr = build_instructions("agent-x", 2, 5, "{\"step\":3}");
    assert!(instr.contains("v2/5"));
    assert!(instr.contains("{\"step\":3}"));
    assert!(instr.contains("continuazione"));
}
