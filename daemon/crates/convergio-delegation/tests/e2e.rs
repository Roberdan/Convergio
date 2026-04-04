//! E2E integration tests for the delegation API endpoints.

use axum::body::Body;
use axum::http::{Request, StatusCode};
use convergio_delegation::routes::{delegation_routes, DelegationState};
use tower::ServiceExt;

fn setup() -> (axum::Router, convergio_db::pool::ConnPool) {
    let pool = convergio_db::pool::create_memory_pool().unwrap();
    let conn = pool.get().unwrap();
    for m in convergio_delegation::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    drop(conn);
    let state = DelegationState {
        pool: pool.clone(),
        event_sink: None,
    };
    let app = delegation_routes(state);
    (app, pool)
}

fn rebuild(pool: &convergio_db::pool::ConnPool) -> axum::Router {
    let state = DelegationState {
        pool: pool.clone(),
        event_sink: None,
    };
    delegation_routes(state)
}

async fn body_json(resp: axum::http::Response<Body>) -> serde_json::Value {
    let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX)
        .await
        .unwrap();
    serde_json::from_slice(&bytes).unwrap()
}

fn post_json(uri: &str, body: &str) -> Request<Body> {
    Request::builder()
        .method("POST")
        .uri(uri)
        .header("content-type", "application/json")
        .body(Body::from(body.to_owned()))
        .unwrap()
}

fn get_req(uri: &str) -> Request<Body> {
    Request::builder().uri(uri).body(Body::empty()).unwrap()
}

#[tokio::test]
async fn test_mark_delegated() {
    let (app, pool) = setup();

    // POST /api/mesh/delegate
    let req = post_json("/api/mesh/delegate", r#"{"plan_id":1,"peer":"test-peer"}"#);
    let resp = app.oneshot(req).await.unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = body_json(resp).await;
    assert_eq!(json["ok"], true);
    assert!(json["delegation_id"].is_string());

    // GET /api/delegate/list — verify delegation appears
    let app2 = rebuild(&pool);
    let resp2 = app2.oneshot(get_req("/api/delegate/list")).await.unwrap();
    assert_eq!(resp2.status(), StatusCode::OK);
    let json2 = body_json(resp2).await;
    assert_eq!(json2["ok"], true);
    let list = json2["delegations"].as_array().unwrap();
    assert_eq!(list.len(), 1);
    assert_eq!(list[0]["peer_name"], "test-peer");
    assert_eq!(list[0]["plan_id"], 1);
}

#[tokio::test]
async fn test_get_status() {
    let (app, pool) = setup();

    // Create a delegation
    let req = post_json("/api/mesh/delegate", r#"{"plan_id":5,"peer":"studio-mac"}"#);
    let resp = app.oneshot(req).await.unwrap();
    let json = body_json(resp).await;
    let del_id = json["delegation_id"].as_str().unwrap();

    // GET /api/delegate/status/:delegation_id
    let app2 = rebuild(&pool);
    let uri = format!("/api/delegate/status/{del_id}");
    let resp2 = app2.oneshot(get_req(&uri)).await.unwrap();
    assert_eq!(resp2.status(), StatusCode::OK);
    let json2 = body_json(resp2).await;
    assert_eq!(json2["ok"], true);
    let rec = &json2["delegation"];
    assert_eq!(rec["delegation_id"], del_id);
    assert_eq!(rec["plan_id"], 5);
    assert_eq!(rec["peer_name"], "studio-mac");
    assert_eq!(rec["status"], "pending");
}

#[tokio::test]
async fn test_list_with_filter() {
    let (app, pool) = setup();

    // Create delegation for plan 1
    let req1 = post_json("/api/mesh/delegate", r#"{"plan_id":1,"peer":"linux-box"}"#);
    app.oneshot(req1).await.unwrap();

    // Create delegation for plan 2
    let app2 = rebuild(&pool);
    let req2 = post_json("/api/mesh/delegate", r#"{"plan_id":2,"peer":"mac-studio"}"#);
    app2.oneshot(req2).await.unwrap();

    // List all — should be 2
    let app3 = rebuild(&pool);
    let resp_all = app3.oneshot(get_req("/api/delegate/list")).await.unwrap();
    let json_all = body_json(resp_all).await;
    assert_eq!(json_all["delegations"].as_array().unwrap().len(), 2);

    // Filter by plan_id=1 — should be 1
    let app4 = rebuild(&pool);
    let resp_f = app4
        .oneshot(get_req("/api/delegate/list?plan_id=1"))
        .await
        .unwrap();
    let json_f = body_json(resp_f).await;
    let filtered = json_f["delegations"].as_array().unwrap();
    assert_eq!(filtered.len(), 1);
    assert_eq!(filtered[0]["plan_id"], 1);
    assert_eq!(filtered[0]["peer_name"], "linux-box");
}

#[tokio::test]
async fn test_spawn_returns_started() {
    let (app, pool) = setup();

    // POST /api/delegate/spawn with a nonexistent peer
    let req = post_json(
        "/api/delegate/spawn",
        r#"{"peer":"nonexistent-peer","plan_id":99}"#,
    );
    let resp = app.oneshot(req).await.unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = body_json(resp).await;
    assert_eq!(json["ok"], true);
    assert_eq!(json["status"], "started");
    let del_id = json["delegation_id"].as_str().unwrap();

    // Wait for background pipeline to attempt and fail
    tokio::time::sleep(std::time::Duration::from_secs(1)).await;

    // GET status — delegation should exist (likely failed)
    let app2 = rebuild(&pool);
    let uri = format!("/api/delegate/status/{del_id}");
    let resp2 = app2.oneshot(get_req(&uri)).await.unwrap();
    assert_eq!(resp2.status(), StatusCode::OK);
    let json2 = body_json(resp2).await;
    assert_eq!(json2["ok"], true);
    assert!(json2["delegation"].is_object());
    assert_eq!(json2["delegation"]["delegation_id"], del_id);
}
