//! E2E HTTP integration tests for plan lifecycle endpoints.
//!
//! Tests the real axum routes via tower::ServiceExt::oneshot against
//! an in-memory SQLite database with full orchestrator migrations.

mod helpers;

use axum::body::Body;
use axum::http::{Request, StatusCode};
use helpers::{app, json_body, post_json, setup};
use tower::ServiceExt;

#[tokio::test]
async fn test_create_plan() {
    let (_, state) = setup();
    let resp = app(&state)
        .oneshot(post_json(
            "/api/plan-db/create",
            r#"{"project_id":"proj-1","name":"widget-plan",
                "objective":"Build widget","motivation":"Customer need",
                "requester":"roberto"}"#,
        ))
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = json_body(resp).await;
    assert_eq!(json["status"], "created");
    assert!(json["id"].as_i64().unwrap() > 0);
}

#[tokio::test]
async fn test_list_plans() {
    let (_, state) = setup();
    // Create two plans
    for name in ["alpha-plan", "beta-plan"] {
        let body = format!(
            r#"{{"project_id":"proj-1","name":"{name}",
                "objective":"obj","motivation":"mot","requester":"rob"}}"#,
        );
        let resp = app(&state)
            .oneshot(post_json("/api/plan-db/create", &body))
            .await
            .unwrap();
        assert_eq!(resp.status(), StatusCode::OK);
    }
    // List
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .uri("/api/plan-db/list")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = json_body(resp).await;
    let plans = json.as_array().expect("list should be an array");
    assert_eq!(plans.len(), 2);
}

#[tokio::test]
async fn test_get_plan() {
    let (_, state) = setup();
    let resp = app(&state)
        .oneshot(post_json(
            "/api/plan-db/create",
            r#"{"project_id":"proj-1","name":"detail-plan",
                "objective":"obj","motivation":"mot","requester":"rob"}"#,
        ))
        .await
        .unwrap();
    let created = json_body(resp).await;
    let plan_id = created["id"].as_i64().unwrap();

    let resp = app(&state)
        .oneshot(
            Request::builder()
                .uri(format!("/api/plan-db/json/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = json_body(resp).await;
    assert_eq!(json["name"], "detail-plan");
    assert_eq!(json["status"], "todo");
}

#[tokio::test]
async fn test_cancel_plan() {
    let (_, state) = setup();
    let resp = app(&state)
        .oneshot(post_json(
            "/api/plan-db/create",
            r#"{"project_id":"proj-1","name":"cancel-me",
                "objective":"obj","motivation":"mot","requester":"rob"}"#,
        ))
        .await
        .unwrap();
    let created = json_body(resp).await;
    let plan_id = created["id"].as_i64().unwrap();

    let resp = app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/cancel/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = json_body(resp).await;
    assert_eq!(json["status"], "cancelled");
}

#[tokio::test]
async fn test_complete_plan() {
    let (_, state) = setup();
    let resp = app(&state)
        .oneshot(post_json(
            "/api/plan-db/create",
            r#"{"project_id":"proj-1","name":"finish-plan",
                "objective":"obj","motivation":"mot","requester":"rob"}"#,
        ))
        .await
        .unwrap();
    let plan_id = json_body(resp).await["id"].as_i64().unwrap();

    let resp = app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/complete/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let json = json_body(resp).await;
    assert_eq!(json["status"], "done");
}
