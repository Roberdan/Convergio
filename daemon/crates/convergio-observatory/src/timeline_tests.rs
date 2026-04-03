//! Tests for the timeline module.

use rusqlite::Connection;

use crate::timeline::{query_timeline, record_event, NewEvent, TimelineFilter};
use crate::types::EventSource;

fn setup_db() -> convergio_db::pool::PooledConn {
    let pool = convergio_db::pool::create_memory_pool().unwrap();
    let conn = pool.get().unwrap();
    convergio_db::migration::ensure_registry(&conn).unwrap();
    convergio_db::migration::apply_migrations(&conn, "observatory", &crate::schema::migrations())
        .unwrap();
    conn
}

fn insert(
    conn: &Connection,
    src: &EventSource,
    etype: &str,
    actor: &str,
    org: Option<&str>,
    node: Option<&str>,
    summary: &str,
) {
    let evt = NewEvent {
        source: src,
        event_type: etype,
        actor,
        org_id: org,
        node_id: node,
        summary,
        details_json: None,
    };
    record_event(conn, &evt).unwrap();
}

#[test]
fn record_and_query_events() {
    let conn = setup_db();
    insert(
        &conn,
        &EventSource::Orchestrator,
        "task_completed",
        "Elena",
        Some("legal-corp"),
        Some("m5max"),
        "Task 42 completed",
    );
    insert(
        &conn,
        &EventSource::Agent,
        "agent_online",
        "Baccio",
        Some("dev-corp"),
        Some("m1pro"),
        "Baccio came online",
    );

    let all = query_timeline(&conn, &TimelineFilter::default()).unwrap();
    assert_eq!(all.len(), 2);

    let filtered = query_timeline(
        &conn,
        &TimelineFilter {
            org_id: Some("legal-corp"),
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(filtered.len(), 1);
    assert_eq!(filtered[0].actor, "Elena");
}

#[test]
fn filter_by_source_and_node() {
    let conn = setup_db();
    for i in 0..5 {
        insert(
            &conn,
            &EventSource::Mesh,
            "sync",
            &format!("peer-{i}"),
            None,
            Some("m5max"),
            &format!("Sync event {i}"),
        );
    }
    insert(
        &conn,
        &EventSource::Security,
        "audit",
        "system",
        None,
        Some("m1pro"),
        "Audit entry",
    );

    let mesh = query_timeline(
        &conn,
        &TimelineFilter {
            source: Some("mesh"),
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(mesh.len(), 5);

    let m1pro = query_timeline(
        &conn,
        &TimelineFilter {
            node_id: Some("m1pro"),
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(m1pro.len(), 1);
}

#[test]
fn limit_works() {
    let conn = setup_db();
    for i in 0..10 {
        insert(
            &conn,
            &EventSource::System,
            "tick",
            "daemon",
            None,
            None,
            &format!("Event {i}"),
        );
    }
    let limited = query_timeline(
        &conn,
        &TimelineFilter {
            limit: 3,
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(limited.len(), 3);
}
