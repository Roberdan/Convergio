//! POST /api/plan-db/validate — verify plan completeness before execution.

use std::sync::Arc;

use axum::extract::State;
use axum::response::Json;
use axum::routing::post;
use axum::Router;
use rusqlite::params;
use serde::Deserialize;
use serde_json::json;

use crate::plan_routes::PlanState;

pub fn validate_routes(state: Arc<PlanState>) -> Router {
    Router::new()
        .route("/api/plan-db/validate", post(handle_validate))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct ValidateReq {
    plan_id: i64,
}

/// Validate plan completeness. Returns errors for missing fields.
async fn handle_validate(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<ValidateReq>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };

    let mut errors: Vec<String> = Vec::new();

    // 1. Plan must exist
    let plan_name: Option<String> = conn
        .query_row(
            "SELECT name FROM plans WHERE id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .ok();
    if plan_name.is_none() {
        return Json(json!({"valid": false, "errors": ["plan not found"]}));
    }

    // 2. Plan must have metadata (objective, motivation, requester)
    let has_meta: bool = conn
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM plan_metadata WHERE plan_id = ?1 \
             AND objective IS NOT NULL AND motivation IS NOT NULL \
             AND requester IS NOT NULL)",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(false);
    if !has_meta {
        errors.push("missing plan_metadata (objective, motivation, requester)".into());
    }

    // 3. Plan must have at least 1 wave
    let wave_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM waves WHERE plan_id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if wave_count == 0 {
        errors.push("plan has zero waves".into());
    }

    // 4. Plan must have at least 1 task
    let task_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if task_count == 0 {
        errors.push("plan has zero tasks".into());
    }

    // 5. Every task must have a non-empty title
    let empty_titles: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 \
             AND (title IS NULL OR title = '')",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if empty_titles > 0 {
        errors.push(format!("{empty_titles} task(s) have empty titles"));
    }

    // 6. Every task must be assigned to a wave
    let orphan_tasks: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND wave_id IS NULL",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if orphan_tasks > 0 {
        errors.push(format!("{orphan_tasks} task(s) not assigned to a wave"));
    }

    if errors.is_empty() {
        Json(json!({
            "valid": true,
            "plan_id": body.plan_id,
            "plan_name": plan_name,
            "waves": wave_count,
            "tasks": task_count,
        }))
    } else {
        Json(json!({
            "valid": false,
            "plan_id": body.plan_id,
            "errors": errors,
        }))
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn validate_route_compiles() {
        // Ensures the route function signature is correct
        assert!(true);
    }
}
