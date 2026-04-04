// HTTP routes for evaluation framework.
// WHY: Exposes planner and Thor quality metrics over REST so CLI,
// UI, and dashboards can query orchestration effectiveness.

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::evaluation;

pub fn evaluation_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/evaluations/record", post(handle_record))
        .route("/api/evaluations/list", get(handle_list))
        .route("/api/evaluations/thor-accuracy", get(handle_thor_accuracy))
        .route("/api/evaluations/planner-rate", get(handle_planner_rate))
        .route(
            "/api/evaluations/review-outcome",
            post(handle_review_outcome),
        )
        .route(
            "/api/evaluations/review-outcomes",
            get(handle_review_outcomes),
        )
        .with_state(pool)
}

#[derive(Deserialize)]
struct RecordBody {
    plan_id: i64,
    #[serde(default = "default_evaluator")]
    evaluator: String,
    #[serde(default)]
    tasks_total: i64,
    #[serde(default)]
    tasks_completed: i64,
    #[serde(default)]
    tasks_failed: i64,
    #[serde(default)]
    false_positives: i64,
    #[serde(default)]
    false_negatives: i64,
    #[serde(default)]
    precision: f64,
    #[serde(default)]
    recall: f64,
    #[serde(default)]
    f1_score: f64,
    #[serde(default)]
    total_cost_usd: f64,
    #[serde(default)]
    total_duration_secs: i64,
}

fn default_evaluator() -> String {
    "system".to_string()
}

async fn handle_record(State(pool): State<ConnPool>, Json(b): Json<RecordBody>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let eval = evaluation::PlanEvaluation {
        id: 0,
        plan_id: b.plan_id,
        evaluator: b.evaluator,
        tasks_total: b.tasks_total,
        tasks_completed: b.tasks_completed,
        tasks_failed: b.tasks_failed,
        false_positives: b.false_positives,
        false_negatives: b.false_negatives,
        precision: b.precision,
        recall: b.recall,
        f1_score: b.f1_score,
        total_cost_usd: b.total_cost_usd,
        total_duration_secs: b.total_duration_secs,
        evaluated_at: String::new(),
    };
    match evaluation::record_evaluation(&conn, &eval) {
        Ok(id) => Json(json!({"ok": true, "id": id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct ListQuery {
    plan_id: Option<i64>,
    #[serde(default = "default_limit")]
    limit: u32,
}

fn default_limit() -> u32 {
    50
}

async fn handle_list(State(pool): State<ConnPool>, Query(q): Query<ListQuery>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let evals = evaluation::list_evaluations(&conn, q.plan_id, q.limit);
    Json(json!({"evaluations": evals}))
}

async fn handle_thor_accuracy(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let acc = evaluation::compute_thor_accuracy(&conn);
    Json(json!({"thor_accuracy": acc}))
}

async fn handle_planner_rate(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rate = evaluation::planner_success_rate(&conn);
    Json(json!({"planner_success_rate": rate}))
}

#[derive(Deserialize)]
struct ReviewOutcomeBody {
    plan_id: i64,
    task_id: i64,
    thor_decision: String,
    actual_outcome: String,
}

async fn handle_review_outcome(
    State(pool): State<ConnPool>,
    Json(b): Json<ReviewOutcomeBody>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match evaluation::record_review_outcome(
        &conn,
        b.plan_id,
        b.task_id,
        &b.thor_decision,
        &b.actual_outcome,
    ) {
        Ok(()) => Json(json!({"ok": true})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct ReviewOutcomesQuery {
    plan_id: Option<i64>,
}

async fn handle_review_outcomes(
    State(pool): State<ConnPool>,
    Query(q): Query<ReviewOutcomesQuery>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let outcomes = evaluation::list_review_outcomes(&conn, q.plan_id);
    Json(json!({"review_outcomes": outcomes}))
}
