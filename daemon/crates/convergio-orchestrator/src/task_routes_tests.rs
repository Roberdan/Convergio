use super::*;
use std::sync::Arc;
use tokio::sync::Notify;

fn setup() -> PlanState {
    let pool = convergio_db::pool::create_memory_pool().unwrap();
    let conn = pool.get().unwrap();
    convergio_db::migration::ensure_registry(&conn).unwrap();
    convergio_db::migration::apply_migrations(&conn, "ipc", &convergio_ipc::schema::migrations())
        .unwrap();
    convergio_db::migration::apply_migrations(&conn, "orchestrator", &crate::schema::migrations())
        .unwrap();
    drop(conn);
    PlanState {
        pool,
        event_sink: None,
        notify: Arc::new(Notify::new()),
    }
}

fn seed_plan_and_task(state: &PlanState) {
    let conn = state.pool.get().unwrap();
    conn.execute(
        "INSERT INTO plans (id, project_id, name, tasks_done, tasks_total) \
         VALUES (1, 'test', 'Test Plan', 0, 2)",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO waves (id, wave_id, plan_id, name, status) \
         VALUES (1, 1, 1, 'wave-1', 'in_progress')",
        [],
    )
    .unwrap();
    conn.execute(
        "INSERT INTO tasks (id, task_id, plan_id, wave_id, title, status) \
         VALUES (1, 1, 1, 1, 'Task A', 'submitted')",
        [],
    )
    .unwrap();
}

#[test]
fn emit_task_lifecycle_increments_tasks_done() {
    let state = setup();
    seed_plan_and_task(&state);

    emit_task_lifecycle(&state, 1);

    let conn = state.pool.get().unwrap();
    let tasks_done: i64 = conn
        .query_row("SELECT tasks_done FROM plans WHERE id = 1", [], |r| {
            r.get(0)
        })
        .unwrap();
    assert_eq!(tasks_done, 1);
}

#[test]
fn emit_task_lifecycle_emits_ipc_event() {
    let state = setup();
    seed_plan_and_task(&state);

    emit_task_lifecycle(&state, 1);

    let history = convergio_ipc::messaging::history(
        &state.pool,
        None,
        Some(crate::reactor::CHANNEL),
        10,
        None,
    )
    .unwrap();
    assert!(!history.is_empty(), "IPC message should be emitted");
    assert!(
        history[0].content.contains("task_done"),
        "event type should be task_done"
    );
    assert!(
        history[0].content.contains("\"plan_id\":1"),
        "should include plan_id"
    );
}

#[test]
fn emit_task_lifecycle_skips_if_no_plan() {
    let state = setup();
    // No plan or task exists — should not panic
    emit_task_lifecycle(&state, 999);
}
