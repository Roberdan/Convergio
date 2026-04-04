//! Aggregation API — metrics, costs, reports (Fase 24d).
//!
//! - GET /api/metrics/cost          — cost breakdown by model/project/day
//! - GET /api/metrics/summary       — total runs, avg duration, cost, status distribution
//! - GET /api/audit/project/:id     — full project audit report
//! - GET /api/learnings             — aggregated key learnings

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::get;
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

pub fn aggregation_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/metrics/cost", get(cost_breakdown))
        .route("/api/metrics/summary", get(summary))
        .route("/api/audit/project/:project_id", get(project_audit))
        .route("/api/learnings", get(learnings))
        .with_state(pool)
}

#[derive(Deserialize, Default)]
struct CostQuery {
    days: Option<u32>,
    project: Option<String>,
    model: Option<String>,
}

async fn cost_breakdown(State(pool): State<ConnPool>, Query(q): Query<CostQuery>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let days = q.days.unwrap_or(30).min(365);
    let cutoff = format!("datetime('now', '-{days} days')");

    // Cost by model
    let by_model = query_rows(
        &conn,
        &format!(
            "SELECT model, SUM(input_tokens) as inp, SUM(output_tokens) as out, \
             SUM(cost_usd) as cost, COUNT(*) as calls \
             FROM token_usage WHERE created_at >= {cutoff} GROUP BY model ORDER BY cost DESC"
        ),
        &[],
        |r| {
            Ok(json!({
                "model": r.get::<_, String>(0)?,
                "input_tokens": r.get::<_, i64>(1)?,
                "output_tokens": r.get::<_, i64>(2)?,
                "cost_usd": r.get::<_, f64>(3)?,
                "calls": r.get::<_, i64>(4)?,
            }))
        },
    );

    // Cost by day
    let by_day = query_rows(
        &conn,
        &format!(
            "SELECT date(created_at) as day, SUM(cost_usd) as cost, COUNT(*) as calls \
             FROM token_usage WHERE created_at >= {cutoff} \
             GROUP BY day ORDER BY day DESC LIMIT 30"
        ),
        &[],
        |r| {
            Ok(json!({
                "day": r.get::<_, String>(0)?,
                "cost_usd": r.get::<_, f64>(1)?,
                "calls": r.get::<_, i64>(2)?,
            }))
        },
    );

    Json(json!({"by_model": by_model, "by_day": by_day}))
}

async fn summary(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let total_plans: i64 = conn
        .query_row("SELECT count(*) FROM plans", [], |r| r.get(0))
        .unwrap_or(0);
    let done_plans: i64 = conn
        .query_row(
            "SELECT count(*) FROM plans WHERE status = 'done'",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let total_tasks: i64 = conn
        .query_row("SELECT count(*) FROM tasks", [], |r| r.get(0))
        .unwrap_or(0);
    let total_cost: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    let total_tokens: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) FROM token_usage",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);
    let active_agents: i64 = conn
        .query_row(
            "SELECT count(DISTINCT agent_id) FROM agent_activity WHERE status = 'started'",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Status distribution
    let status_dist = query_rows(
        &conn,
        "SELECT status, count(*) FROM plans GROUP BY status",
        &[],
        |r| {
            Ok(json!({
                "status": r.get::<_, String>(0)?,
                "count": r.get::<_, i64>(1)?,
            }))
        },
    );

    Json(json!({
        "total_plans": total_plans,
        "done_plans": done_plans,
        "total_tasks": total_tasks,
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "active_agents": active_agents,
        "plan_status_distribution": status_dist,
    }))
}

async fn project_audit(
    State(pool): State<ConnPool>,
    Path(project_id): Path<String>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let plans = query_rows(
        &conn,
        "SELECT p.id, p.name, p.status, p.created_at, \
         m.objective, m.requester, m.key_learnings_json, \
         COALESCE((SELECT SUM(cost_usd) FROM token_usage WHERE plan_id = p.id), 0) as cost \
         FROM plans p LEFT JOIN plan_metadata m ON m.plan_id = p.id \
         WHERE p.project_id = ?1 ORDER BY p.id",
        &[&project_id as &dyn rusqlite::types::ToSql],
        |r| {
            Ok(json!({
                "id": r.get::<_, i64>(0)?,
                "name": r.get::<_, String>(1)?,
                "status": r.get::<_, String>(2)?,
                "created_at": r.get::<_, String>(3)?,
                "objective": r.get::<_, Option<String>>(4)?,
                "requester": r.get::<_, Option<String>>(5)?,
                "key_learnings": r.get::<_, Option<String>>(6)?,
                "cost_usd": r.get::<_, f64>(7)?,
            }))
        },
    );
    Json(json!({"project_id": project_id, "plans": plans}))
}

async fn learnings(State(pool): State<ConnPool>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows = query_rows(
        &conn,
        "SELECT p.id, p.name, p.project_id, m.key_learnings_json \
         FROM plan_metadata m JOIN plans p ON p.id = m.plan_id \
         WHERE m.key_learnings_json IS NOT NULL AND m.key_learnings_json != '' \
         ORDER BY p.id DESC LIMIT 100",
        &[],
        |r| {
            Ok(json!({
                "plan_id": r.get::<_, i64>(0)?,
                "plan_name": r.get::<_, String>(1)?,
                "project_id": r.get::<_, Option<String>>(2)?,
                "key_learnings": r.get::<_, String>(3)?,
            }))
        },
    );
    Json(json!({"learnings": rows}))
}

/// Helper: run a query and collect rows as JSON values.
fn query_rows(
    conn: &rusqlite::Connection,
    sql: &str,
    params: &[&dyn rusqlite::types::ToSql],
    map: impl Fn(&rusqlite::Row) -> rusqlite::Result<Value>,
) -> Vec<Value> {
    let mut stmt = match conn.prepare(sql) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    let result: Vec<Value> = match stmt.query_map(params, map) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    result
}
