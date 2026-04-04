//! PM (Project Manager) agent endpoints — analyze, digest, learnings, cost forecast.

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

pub fn pm_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/pm/analyze/:plan_id", post(analyze_plan))
        .route("/api/pm/digest", get(weekly_digest))
        .route("/api/pm/learnings", get(aggregated_learnings))
        .route("/api/pm/cost-forecast", get(cost_forecast))
        .with_state(pool)
}

/// Analyze a plan: cost breakdown, duration, evidence gaps, agent activity.
async fn analyze_plan(State(pool): State<ConnPool>, Path(plan_id): Path<i64>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };

    // Cost breakdown
    let total_cost: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage WHERE plan_id = ?1",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    let total_tokens: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) FROM token_usage WHERE plan_id = ?1",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Task counts by status
    let tasks_done: i64 = conn
        .query_row(
            "SELECT count(*) FROM tasks WHERE plan_id = ?1 AND status = 'done'",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let tasks_total: i64 = conn
        .query_row(
            "SELECT count(*) FROM tasks WHERE plan_id = ?1",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Evidence gaps: tasks without evidence
    let tasks_no_evidence: i64 = conn
        .query_row(
            "SELECT count(*) FROM tasks t WHERE t.plan_id = ?1 AND t.status IN ('done','submitted') \
             AND NOT EXISTS (SELECT 1 FROM task_evidence e WHERE e.task_id = t.id)",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Distinct agents
    let agents: i64 = conn
        .query_row(
            "SELECT count(DISTINCT agent) FROM token_usage WHERE plan_id = ?1",
            [plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Plan metadata
    let (objective, requester) = conn
        .query_row(
            "SELECT objective, requester FROM plan_metadata WHERE plan_id = ?1",
            [plan_id],
            |r| {
                Ok((
                    r.get::<_, Option<String>>(0)?,
                    r.get::<_, Option<String>>(1)?,
                ))
            },
        )
        .unwrap_or((None, None));

    Json(json!({
        "plan_id": plan_id,
        "objective": objective,
        "requester": requester,
        "cost_usd": total_cost,
        "total_tokens": total_tokens,
        "tasks_done": tasks_done,
        "tasks_total": tasks_total,
        "completion_pct": if tasks_total > 0 { (tasks_done as f64 / tasks_total as f64 * 100.0).round() } else { 0.0 },
        "evidence_gaps": tasks_no_evidence,
        "agents_involved": agents,
    }))
}

#[derive(Deserialize, Default)]
struct DigestQuery {
    #[allow(dead_code)]
    period: Option<String>,
}

/// Weekly digest: plans completed, cost, learnings, anomalies.
async fn weekly_digest(State(pool): State<ConnPool>, Query(_q): Query<DigestQuery>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };

    let plans_completed: i64 = conn
        .query_row(
            "SELECT count(*) FROM plans WHERE status = 'done' \
             AND updated_at >= datetime('now', '-7 days')",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let week_cost: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage \
             WHERE created_at >= datetime('now', '-7 days')",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    let week_tokens: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) FROM token_usage \
             WHERE created_at >= datetime('now', '-7 days')",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let active_agents: i64 = conn
        .query_row(
            "SELECT count(DISTINCT agent) FROM token_usage \
             WHERE created_at >= datetime('now', '-7 days')",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);

    Json(json!({
        "period": "last_7_days",
        "plans_completed": plans_completed,
        "cost_usd": week_cost,
        "tokens": week_tokens,
        "active_agents": active_agents,
    }))
}

/// Aggregated learnings across all plans with key_learnings_json.
async fn aggregated_learnings(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT p.id, p.name, m.key_learnings_json FROM plan_metadata m \
         JOIN plans p ON p.id = m.plan_id \
         WHERE m.key_learnings_json IS NOT NULL AND m.key_learnings_json != '' \
         ORDER BY p.id DESC LIMIT 50",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map([], |r| {
        Ok(json!({
            "plan_id": r.get::<_, i64>(0)?,
            "plan_name": r.get::<_, String>(1)?,
            "learnings": r.get::<_, String>(2)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"learnings": rows, "count": rows.len()}))
}

#[derive(Deserialize, Default)]
struct ForecastQuery {
    plan_id: Option<i64>,
}

/// Cost forecast based on historical data.
async fn cost_forecast(
    State(pool): State<ConnPool>,
    Query(q): Query<ForecastQuery>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // Average cost per plan
    let avg_cost: f64 = conn
        .query_row(
            "SELECT COALESCE(AVG(plan_cost), 0) FROM (\
             SELECT plan_id, SUM(cost_usd) as plan_cost FROM token_usage \
             WHERE plan_id IS NOT NULL GROUP BY plan_id)",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    // If plan_id given, forecast remaining cost based on completion %
    let forecast = if let Some(pid) = q.plan_id {
        let done: f64 = conn
            .query_row(
                "SELECT CAST(count(*) FILTER (WHERE status='done') AS REAL) / \
                 MAX(count(*), 1) FROM tasks WHERE plan_id = ?1",
                [pid],
                |r| r.get(0),
            )
            .unwrap_or(0.0);
        let spent: f64 = conn
            .query_row(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage WHERE plan_id = ?1",
                [pid],
                |r| r.get(0),
            )
            .unwrap_or(0.0);
        let projected = if done > 0.0 { spent / done } else { avg_cost };
        json!({"plan_id": pid, "spent_usd": spent, "completion_pct": (done * 100.0).round(), "projected_total_usd": projected})
    } else {
        json!({"avg_cost_per_plan_usd": avg_cost})
    };

    Json(json!({"forecast": forecast}))
}
