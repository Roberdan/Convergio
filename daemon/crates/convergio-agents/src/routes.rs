//! HTTP routes for the agent catalog.
//!
//! Mounts under `/api/agents/catalog`.

use axum::extract::{Path, Query, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::get;
use axum::{Json, Router};
use convergio_db::pool::ConnPool;

use crate::types::{AgentInput, AgentQuery};

/// Build all catalog routes.
pub fn catalog_routes(pool: ConnPool) -> Router {
    Router::new()
        .route(
            "/api/agents/catalog",
            get(list_agents).post(create_agent),
        )
        .route(
            "/api/agents/catalog/{name}",
            get(get_agent).put(update_agent).delete(delete_agent),
        )
        .with_state(pool)
}

async fn list_agents(
    State(pool): State<ConnPool>,
    Query(query): Query<AgentQuery>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let agents = crate::store::list_agents(&conn, &query)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(agents))
}

async fn get_agent(
    State(pool): State<ConnPool>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let agent = crate::store::get_agent(&conn, &name)
        .map_err(|_| (StatusCode::NOT_FOUND, format!("agent '{name}' not found")))?;
    Ok::<_, (StatusCode, String)>(Json(agent))
}

async fn create_agent(
    State(pool): State<ConnPool>,
    Json(input): Json<AgentInput>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let id = crate::store::create_agent(&conn, &input)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>((
        StatusCode::CREATED,
        Json(serde_json::json!({ "id": id })),
    ))
}

async fn update_agent(
    State(pool): State<ConnPool>,
    Path(name): Path<String>,
    Json(input): Json<AgentInput>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let updated = crate::store::update_agent(&conn, &name, &input)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    if updated {
        Ok::<_, (StatusCode, String)>(StatusCode::NO_CONTENT)
    } else {
        Err((StatusCode::NOT_FOUND, format!("agent '{name}' not found")))
    }
}

async fn delete_agent(
    State(pool): State<ConnPool>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let deleted = crate::store::delete_agent(&conn, &name)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    if deleted {
        Ok::<_, (StatusCode, String)>(StatusCode::NO_CONTENT)
    } else {
        Err((StatusCode::NOT_FOUND, format!("agent '{name}' not found")))
    }
}
