//! Shared test helpers for plan lifecycle E2E tests.

use std::sync::Arc;

use axum::body::Body;
use axum::http::Request;
use axum::Router;
use convergio_db::pool::{create_memory_pool, ConnPool};
use convergio_orchestrator::plan_routes::{plan_routes, PlanState};
use convergio_orchestrator::plan_routes_ext::plan_routes_ext;
use convergio_orchestrator::task_routes::task_routes;

/// Create an in-memory database with all orchestrator migrations applied.
pub fn setup() -> (ConnPool, Arc<PlanState>) {
    let pool = create_memory_pool().unwrap();
    let conn = pool.get().unwrap();
    // Schema registry for migration tracking
    convergio_db::migration::ensure_registry(&conn).unwrap();
    // Core orchestrator tables (v1-v3)
    let base = convergio_orchestrator::schema::migrations();
    convergio_db::migration::apply_migrations(&conn, "orchestrator", &base).unwrap();
    // Tracking tables (v4-v8): plan_metadata, token_usage, etc.
    let tracking = convergio_orchestrator::schema_tracking::tracking_migrations();
    convergio_db::migration::apply_migrations(&conn, "orchestrator", &tracking).unwrap();
    // IPC tables needed by task lifecycle emit
    let ipc = convergio_ipc::schema::migrations();
    convergio_db::migration::apply_migrations(&conn, "ipc", &ipc).unwrap();
    drop(conn);
    let state = Arc::new(PlanState {
        pool: pool.clone(),
        event_sink: None,
        notify: Arc::new(tokio::sync::Notify::new()),
    });
    (pool, state)
}

/// Build the test router merging plan, plan_ext and task routes.
pub fn app(state: &Arc<PlanState>) -> Router {
    plan_routes(state.clone())
        .merge(plan_routes_ext(state.clone()))
        .merge(task_routes(state.clone()))
}

/// Build a POST request with JSON body.
pub fn post_json(uri: &str, body: &str) -> Request<Body> {
    Request::builder()
        .method("POST")
        .uri(uri)
        .header("content-type", "application/json")
        .body(Body::from(body.to_owned()))
        .unwrap()
}

/// Extract JSON from response body.
pub async fn json_body(resp: axum::http::Response<Body>) -> serde_json::Value {
    let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX)
        .await
        .unwrap();
    serde_json::from_slice(&bytes).unwrap()
}
