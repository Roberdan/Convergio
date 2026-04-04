//! Tracking routes — token usage, agent activity, plan metadata, reports.

use axum::extract::{Path, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

pub fn tracking_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/tracking/tokens", post(record_tokens))
        .route("/api/tracking/agent-activity", post(record_activity))
        .route("/api/plan-db/metadata", post(upsert_metadata))
        .route("/api/plan-db/metadata/:plan_id", get(get_metadata))
        .route("/api/plan-db/report", post(write_report))
        .route("/api/plan-db/report/:plan_id", get(get_report))
        .with_state(pool)
}

#[derive(Deserialize)]
struct TokenUsageBody {
    plan_id: Option<i64>,
    wave_id: Option<i64>,
    task_id: Option<i64>,
    agent: String,
    model: String,
    input_tokens: i64,
    output_tokens: i64,
    #[serde(default)]
    cost_usd: f64,
    execution_host: Option<String>,
}

async fn record_tokens(State(pool): State<ConnPool>, Json(b): Json<TokenUsageBody>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO token_usage \
         (plan_id, wave_id, task_id, agent, model, input_tokens, output_tokens, \
          cost_usd, execution_host) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        rusqlite::params![
            b.plan_id,
            b.wave_id,
            b.task_id,
            b.agent,
            b.model,
            b.input_tokens,
            b.output_tokens,
            b.cost_usd,
            b.execution_host,
        ],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            Json(json!({"ok": true, "id": id}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct AgentActivityBody {
    agent_id: String,
    agent_type: Option<String>,
    plan_id: Option<i64>,
    task_id: Option<i64>,
    action: String,
    #[serde(default = "default_started")]
    status: String,
    model: Option<String>,
    #[serde(default)]
    tokens_in: i64,
    #[serde(default)]
    tokens_out: i64,
    #[serde(default)]
    cost_usd: f64,
    completed_at: Option<String>,
    duration_s: Option<f64>,
    host: Option<String>,
    exit_reason: Option<String>,
    metadata_json: Option<String>,
}

fn default_started() -> String {
    "started".into()
}

async fn record_activity(
    State(pool): State<ConnPool>,
    Json(b): Json<AgentActivityBody>,
) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO agent_activity \
         (agent_id, agent_type, plan_id, task_id, action, status, model, \
          tokens_in, tokens_out, cost_usd, completed_at, duration_s, host, \
          exit_reason, metadata_json) \
         VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15)",
        rusqlite::params![
            b.agent_id,
            b.agent_type,
            b.plan_id,
            b.task_id,
            b.action,
            b.status,
            b.model,
            b.tokens_in,
            b.tokens_out,
            b.cost_usd,
            b.completed_at,
            b.duration_s,
            b.host,
            b.exit_reason,
            b.metadata_json,
        ],
    ) {
        Ok(_) => Json(json!({"ok": true, "id": conn.last_insert_rowid()})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct MetadataBody {
    plan_id: i64,
    objective: Option<String>,
    motivation: Option<String>,
    requester: Option<String>,
    created_by: Option<String>,
    approved_by: Option<String>,
    key_learnings_json: Option<String>,
}

async fn upsert_metadata(State(pool): State<ConnPool>, Json(b): Json<MetadataBody>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO plan_metadata (plan_id, objective, motivation, requester, \
         created_by, approved_by, key_learnings_json) \
         VALUES (?1,?2,?3,?4,?5,?6,?7) \
         ON CONFLICT(plan_id) DO UPDATE SET \
         objective=COALESCE(excluded.objective, objective), \
         motivation=COALESCE(excluded.motivation, motivation), \
         requester=COALESCE(excluded.requester, requester), \
         created_by=COALESCE(excluded.created_by, created_by), \
         approved_by=COALESCE(excluded.approved_by, approved_by), \
         key_learnings_json=COALESCE(excluded.key_learnings_json, key_learnings_json)",
        rusqlite::params![
            b.plan_id,
            b.objective,
            b.motivation,
            b.requester,
            b.created_by,
            b.approved_by,
            b.key_learnings_json,
        ],
    ) {
        Ok(_) => Json(json!({"ok": true, "plan_id": b.plan_id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn get_metadata(State(pool): State<ConnPool>, Path(plan_id): Path<i64>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.query_row(
        "SELECT plan_id, objective, motivation, requester, created_by, \
         approved_by, key_learnings_json, report_json, closed_at \
         FROM plan_metadata WHERE plan_id = ?1",
        [plan_id],
        |r| {
            Ok(json!({
                "plan_id": r.get::<_, i64>(0)?,
                "objective": r.get::<_, Option<String>>(1)?,
                "motivation": r.get::<_, Option<String>>(2)?,
                "requester": r.get::<_, Option<String>>(3)?,
                "created_by": r.get::<_, Option<String>>(4)?,
                "approved_by": r.get::<_, Option<String>>(5)?,
                "key_learnings_json": r.get::<_, Option<String>>(6)?,
                "report_json": r.get::<_, Option<String>>(7)?,
                "closed_at": r.get::<_, Option<String>>(8)?,
            }))
        },
    ) {
        Ok(meta) => Json(json!({"metadata": meta})),
        Err(_) => Json(json!({"error": "metadata not found"})),
    }
}

#[derive(Deserialize)]
struct ReportBody {
    plan_id: i64,
    report_json: String,
    close: Option<bool>,
}

async fn write_report(State(pool): State<ConnPool>, Json(b): Json<ReportBody>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let close_clause = if b.close.unwrap_or(false) {
        ", closed_at = datetime('now')"
    } else {
        ""
    };
    let sql = format!("UPDATE plan_metadata SET report_json = ?1{close_clause} WHERE plan_id = ?2");
    match conn.execute(&sql, rusqlite::params![b.report_json, b.plan_id]) {
        Ok(0) => Json(json!({"error": "plan metadata not found — create metadata first"})),
        Ok(n) => Json(json!({"ok": true, "updated": n})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn get_report(State(pool): State<ConnPool>, Path(plan_id): Path<i64>) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.query_row(
        "SELECT report_json, closed_at FROM plan_metadata WHERE plan_id = ?1",
        [plan_id],
        |r| {
            Ok(json!({
                "plan_id": plan_id,
                "report_json": r.get::<_, Option<String>>(0)?,
                "closed_at": r.get::<_, Option<String>>(1)?,
            }))
        },
    ) {
        Ok(report) => Json(json!({"report": report})),
        Err(_) => Json(json!({"error": "report not found"})),
    }
}
