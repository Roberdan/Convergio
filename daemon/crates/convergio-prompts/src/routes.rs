//! HTTP routes for prompt management and skill registry.
//!
//! Mounts under `/api/prompts` and `/api/skills`.

use axum::extract::{Path, Query, State};
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;

use crate::types::{PromptInput, PromptQuery, SkillInput, SkillQuery};

/// Build all prompt + skill routes.
pub fn routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/prompts", post(create_prompt).get(list_prompts))
        .route("/api/prompts/:id", get(get_prompt).delete(delete_prompt))
        .route("/api/prompts/active/:name", get(get_active_prompt))
        .route("/api/skills", post(register_skill).get(search_skills))
        .route("/api/skills/search", get(search_skills_query))
        .with_state(pool)
}

async fn create_prompt(
    State(pool): State<ConnPool>,
    Json(input): Json<PromptInput>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let id = crate::store::create_prompt(&conn, &input)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>((StatusCode::CREATED, Json(serde_json::json!({ "id": id }))))
}

async fn get_prompt(State(pool): State<ConnPool>, Path(id): Path<String>) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let prompt = crate::store::get_prompt(&conn, &id)
        .map_err(|_| (StatusCode::NOT_FOUND, "prompt not found".to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(prompt))
}

async fn get_active_prompt(
    State(pool): State<ConnPool>,
    Path(name): Path<String>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let prompt = crate::store::get_active_prompt(&conn, &name)
        .map_err(|_| (StatusCode::NOT_FOUND, "no active prompt".to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(prompt))
}

async fn list_prompts(
    State(pool): State<ConnPool>,
    Query(query): Query<PromptQuery>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let prompts = crate::store::list_prompts(&conn, &query)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(prompts))
}

async fn delete_prompt(State(pool): State<ConnPool>, Path(id): Path<String>) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let deleted = crate::store::delete_prompt(&conn, &id)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    if deleted {
        Ok::<_, (StatusCode, String)>(StatusCode::NO_CONTENT)
    } else {
        Err((StatusCode::NOT_FOUND, "prompt not found".to_string()))
    }
}

async fn register_skill(
    State(pool): State<ConnPool>,
    Json(input): Json<SkillInput>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let id = crate::skills::register_skill(&conn, &input)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>((StatusCode::CREATED, Json(serde_json::json!({ "id": id }))))
}

async fn search_skills(
    State(pool): State<ConnPool>,
    Query(query): Query<SkillQuery>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let skills = crate::skills::search_skills(&conn, &query)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(skills))
}

async fn search_skills_query(
    State(pool): State<ConnPool>,
    Query(query): Query<SkillQuery>,
) -> impl IntoResponse {
    let conn = pool
        .get()
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let skills = crate::skills::search_skills(&conn, &query)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    Ok::<_, (StatusCode, String)>(Json(skills))
}
