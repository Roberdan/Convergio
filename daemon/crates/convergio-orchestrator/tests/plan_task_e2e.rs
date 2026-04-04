//! E2E HTTP integration tests for task creation and plan lifecycle
//! transitions that require task + Thor pre-review setup.

mod helpers;

use axum::body::Body;
use axum::http::{Request, StatusCode};
use helpers::{app, json_body, post_json, setup};
use rusqlite::params;
use tower::ServiceExt;

/// Helper: create a plan and return its id.
async fn create_plan(
    state: &std::sync::Arc<convergio_orchestrator::plan_routes::PlanState>,
) -> i64 {
    let resp = app(state)
        .oneshot(post_json(
            "/api/plan-db/create",
            r#"{"project_id":"proj-1","name":"task-plan",
                "objective":"obj","motivation":"mot","requester":"rob"}"#,
        ))
        .await
        .unwrap();
    json_body(resp).await["id"].as_i64().unwrap()
}

#[tokio::test]
async fn test_task_create() {
    let (_, state) = setup();
    let plan_id = create_plan(&state).await;

    // Create a wave first (tasks reference wave_id)
    let wave_body = format!(r#"{{"plan_id":{plan_id},"wave_id":"W-1","name":"wave-alpha"}}"#,);
    let resp = app(&state)
        .oneshot(post_json("/api/plan-db/wave/create", &wave_body))
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let wave = json_body(resp).await;
    let wave_db_id = wave["id"].as_i64().unwrap();

    // Create a task
    let task_body = format!(
        r#"{{"plan_id":{plan_id},"wave_id":{wave_db_id},
            "title":"Implement feature X","description":"Full impl"}}"#,
    );
    let resp = app(&state)
        .oneshot(post_json("/api/plan-db/task/create", &task_body))
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let task = json_body(resp).await;
    assert!(task["id"].as_i64().unwrap() > 0);
}

#[tokio::test]
async fn test_plan_lifecycle_with_thor_review() {
    let (pool, state) = setup();
    let plan_id = create_plan(&state).await;

    // Verify initial status is todo
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .uri(format!("/api/plan-db/json/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(json_body(resp).await["status"], "todo");

    // Create wave + task (StartGate requires >= 1 task)
    let wave_body = format!(r#"{{"plan_id":{plan_id},"wave_id":"W-1","name":"wave-1"}}"#,);
    let wave = json_body(
        app(&state)
            .oneshot(post_json("/api/plan-db/wave/create", &wave_body))
            .await
            .unwrap(),
    )
    .await;
    let wid = wave["id"].as_i64().unwrap();

    let task_body = format!(r#"{{"plan_id":{plan_id},"wave_id":{wid},"title":"Task 1"}}"#,);
    app(&state)
        .oneshot(post_json("/api/plan-db/task/create", &task_body))
        .await
        .unwrap();

    // Start without Thor review should fail
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/start/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    let body = json_body(resp).await;
    assert_eq!(body["gate"], "ThorPreReview");

    // Insert a passing Thor pre-review into plan_metadata
    let conn = pool.get().unwrap();
    conn.execute(
        "UPDATE plan_metadata SET report_json = ?1 WHERE plan_id = ?2",
        params![
            r#"{"pre_review":true,"verdict":"pass","notes":"ok"}"#,
            plan_id
        ],
    )
    .unwrap();
    drop(conn);

    // Now start should succeed
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/start/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::OK);
    let body = json_body(resp).await;
    assert_eq!(body["status"], "in_progress");

    // Complete the plan
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
    assert_eq!(json_body(resp).await["status"], "done");
}

#[tokio::test]
async fn test_start_gate_blocks_without_tasks() {
    let (pool, state) = setup();
    let plan_id = create_plan(&state).await;

    // Insert passing Thor review
    let conn = pool.get().unwrap();
    conn.execute(
        "UPDATE plan_metadata SET report_json = ?1 WHERE plan_id = ?2",
        params![r#"{"pre_review":true,"verdict":"pass"}"#, plan_id],
    )
    .unwrap();
    drop(conn);

    // Start should fail: no tasks
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/start/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    let body = json_body(resp).await;
    assert_eq!(body["gate"], "StartGate");
}

#[tokio::test]
async fn test_list_plans_filter_by_status() {
    let (_, state) = setup();
    // Create and cancel one plan
    let plan_id = create_plan(&state).await;
    app(&state)
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(format!("/api/plan-db/cancel/{plan_id}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    // Create another plan (stays todo)
    create_plan(&state).await;

    // Filter by cancelled
    let resp = app(&state)
        .oneshot(
            Request::builder()
                .uri("/api/plan-db/list?status=cancelled")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    let plans = json_body(resp).await;
    let arr = plans.as_array().unwrap();
    assert_eq!(arr.len(), 1);
    assert_eq!(arr[0]["status"], "cancelled");
}
