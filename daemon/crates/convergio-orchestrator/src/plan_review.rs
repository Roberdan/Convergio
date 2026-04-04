//! Thor plan-level review — pre-execution and post-execution validation.
//!
//! - POST /api/plan-db/review          — pre-execution review (plan completeness)
//! - POST /api/plan-db/validate-completion — post-execution review (evidence check)

use std::sync::Arc;

use axum::extract::State;
use axum::response::Json;
use axum::routing::post;
use axum::Router;
use rusqlite::params;
use serde::Deserialize;
use serde_json::json;

use crate::plan_routes::PlanState;

pub fn review_routes(state: Arc<PlanState>) -> Router {
    Router::new()
        .route("/api/plan-db/review", post(handle_review))
        .route(
            "/api/plan-db/validate-completion",
            post(handle_validate_completion),
        )
        .with_state(state)
}

#[derive(Debug, Deserialize)]
struct ReviewReq {
    plan_id: i64,
}

/// Thor pre-execution review. Checks plan completeness before starting.
async fn handle_review(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<ReviewReq>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut findings: Vec<String> = Vec::new();
    let mut recommendations: Vec<String> = Vec::new();

    // 1. Check metadata exists
    let has_meta: bool = conn
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM plan_metadata WHERE plan_id = ?1 \
             AND objective IS NOT NULL)",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(false);
    if !has_meta {
        findings.push("missing objective/motivation/requester".into());
    }

    // 2. Check task count
    let task_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if task_count == 0 {
        findings.push("plan has zero tasks".into());
    }

    // 3. Check wave count
    let wave_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM waves WHERE plan_id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if wave_count == 0 {
        findings.push("plan has zero waves".into());
    }

    // 4. Check for tasks without wave
    let orphans: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND wave_id IS NULL",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if orphans > 0 {
        findings.push(format!("{orphans} task(s) not assigned to a wave"));
    }

    // 5. Check for empty titles
    let empty_titles: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND (title IS NULL OR title = '')",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if empty_titles > 0 {
        findings.push(format!("{empty_titles} task(s) have empty titles"));
    }

    // Recommendations
    if task_count > 0 && wave_count > 0 && findings.is_empty() {
        recommendations.push("plan looks complete — ready for execution".into());
    }

    let verdict = if findings.is_empty() { "pass" } else { "fail" };

    // Save report to plan_metadata
    let report = json!({
        "type": "pre_review",
        "verdict": verdict,
        "findings": findings,
        "recommendations": recommendations,
        "tasks": task_count,
        "waves": wave_count,
    });
    let _ = conn.execute(
        "UPDATE plan_metadata SET report_json = ?1 WHERE plan_id = ?2",
        params![report.to_string(), body.plan_id],
    );

    Json(json!({
        "verdict": verdict,
        "findings": findings,
        "recommendations": recommendations,
        "plan_id": body.plan_id,
    }))
}

/// Thor post-execution review. Checks evidence after all tasks are done.
async fn handle_validate_completion(
    State(state): State<Arc<PlanState>>,
    Json(body): Json<ReviewReq>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut findings: Vec<String> = Vec::new();

    // 1. All tasks must be done or submitted
    let incomplete: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 \
             AND status NOT IN ('done', 'submitted', 'cancelled', 'skipped')",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if incomplete > 0 {
        findings.push(format!("{incomplete} task(s) still incomplete"));
    }

    // 2. Every done/submitted task should have evidence
    let no_evidence: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks t WHERE t.plan_id = ?1 \
             AND t.status IN ('done', 'submitted') \
             AND NOT EXISTS (SELECT 1 FROM task_evidence e WHERE e.task_db_id = t.id)",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if no_evidence > 0 {
        findings.push(format!("{no_evidence} task(s) have no evidence"));
    }

    // 3. Total cost assessment
    let total_cost: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage WHERE plan_id = ?1",
            params![body.plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0.0);

    let verdict = if findings.is_empty() { "pass" } else { "fail" };

    // Save report
    let report = json!({
        "type": "post_review",
        "verdict": verdict,
        "findings": findings,
        "total_cost_usd": total_cost,
    });
    let _ = conn.execute(
        "UPDATE plan_metadata SET report_json = ?1 WHERE plan_id = ?2",
        params![report.to_string(), body.plan_id],
    );

    Json(json!({
        "verdict": verdict,
        "findings": findings,
        "cost_assessment": {"total_usd": total_cost},
        "plan_id": body.plan_id,
    }))
}
