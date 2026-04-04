//! HTTP API routes for convergio-org.
//!
//! - POST   /api/orgs                      — create org
//! - GET    /api/orgs                      — list orgs
//! - GET    /api/orgs/:id                  — get org with members
//! - PUT    /api/orgs/:id                  — update org
//! - POST   /api/orgs/:id/members          — add member
//! - DELETE  /api/orgs/:id/members/:agent   — remove member
//! - GET    /api/orgs/:id/orgchart         — render orgchart
//! - POST   /api/notify                    — queue notification
//! - GET    /api/notify/queue              — list pending notifications
//! - POST   /api/decisions                 — log decision
//! - GET    /api/decisions                 — query decisions

use std::sync::Arc;

use axum::extract::{Path, Query, State};
use axum::response::Json;
use axum::routing::{delete, get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

pub struct OrgState {
    pub pool: ConnPool,
}

pub fn org_routes(state: Arc<OrgState>) -> Router {
    Router::new()
        .route("/api/orgs", post(create_org).get(list_orgs))
        .route("/api/orgs/:id", get(get_org).put(update_org))
        .route("/api/orgs/:id/members", post(add_member))
        .route("/api/orgs/:id/members/:agent", delete(remove_member))
        .route("/api/orgs/:id/orgchart", get(get_orgchart))
        .route("/api/notify", post(queue_notification))
        .route("/api/notify/queue", get(list_notifications))
        .route("/api/decisions", post(log_decision).get(query_decisions))
        .with_state(state)
}

// --- Org CRUD (uses ipc_orgs / ipc_org_members tables) ---

#[derive(Deserialize)]
struct CreateOrgBody {
    id: String,
    mission: String,
    #[serde(default)]
    objectives: String,
    ceo_agent: String,
    #[serde(default)]
    budget: f64,
    #[serde(default = "default_daily_tokens")]
    daily_budget_tokens: i64,
}

fn default_daily_tokens() -> i64 {
    1000
}

async fn create_org(
    State(s): State<Arc<OrgState>>,
    Json(body): Json<CreateOrgBody>,
) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO ipc_orgs (id, mission, objectives, ceo_agent, budget, daily_budget_tokens) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        rusqlite::params![
            body.id,
            body.mission,
            body.objectives,
            body.ceo_agent,
            body.budget,
            body.daily_budget_tokens,
        ],
    ) {
        Ok(_) => Json(json!({"ok": true, "id": body.id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn list_orgs(State(s): State<Arc<OrgState>>) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT id, mission, ceo_agent, budget, status, created_at FROM ipc_orgs ORDER BY id",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map([], |r| {
        Ok(json!({
            "id": r.get::<_, String>(0)?,
            "mission": r.get::<_, String>(1)?,
            "ceo_agent": r.get::<_, String>(2)?,
            "budget": r.get::<_, f64>(3)?,
            "status": r.get::<_, String>(4)?,
            "created_at": r.get::<_, String>(5)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"orgs": rows}))
}

async fn get_org(
    State(s): State<Arc<OrgState>>,
    Path(id): Path<String>,
) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let org = conn.query_row(
        "SELECT id, mission, objectives, ceo_agent, budget, daily_budget_tokens, status, \
         created_at, updated_at FROM ipc_orgs WHERE id = ?1",
        [&id],
        |r| {
            Ok(json!({
                "id": r.get::<_, String>(0)?,
                "mission": r.get::<_, String>(1)?,
                "objectives": r.get::<_, String>(2)?,
                "ceo_agent": r.get::<_, String>(3)?,
                "budget": r.get::<_, f64>(4)?,
                "daily_budget_tokens": r.get::<_, i64>(5)?,
                "status": r.get::<_, String>(6)?,
                "created_at": r.get::<_, String>(7)?,
                "updated_at": r.get::<_, String>(8)?,
            }))
        },
    );
    match org {
        Ok(org) => {
            let members = crate::routes_members::load_members(&conn, &id);
            Json(json!({"org": org, "members": members}))
        }
        Err(_) => Json(json!({"error": "org not found"})),
    }
}

async fn update_org(
    State(s): State<Arc<OrgState>>,
    Path(id): Path<String>,
    Json(body): Json<crate::routes_members::UpdateOrgBody>,
) -> Json<Value> {
    crate::routes_members::update_org(&s.pool, &id, body)
}

// --- Members (delegated to routes_members) ---

async fn add_member(
    State(s): State<Arc<OrgState>>,
    Path(id): Path<String>,
    Json(body): Json<crate::routes_members::AddMemberBody>,
) -> Json<Value> {
    crate::routes_members::add_member(&s.pool, &id, body)
}

async fn remove_member(
    State(s): State<Arc<OrgState>>,
    Path((id, agent)): Path<(String, String)>,
) -> Json<Value> {
    crate::routes_members::remove_member(&s.pool, &id, &agent)
}

async fn get_orgchart(
    State(s): State<Arc<OrgState>>,
    Path(id): Path<String>,
) -> Json<Value> {
    crate::routes_members::get_orgchart(&s.pool, &id)
}

// --- Notifications (notification_queue table) ---

async fn queue_notification(
    State(s): State<Arc<OrgState>>,
    Json(body): Json<crate::routes_notify::NotifyBody>,
) -> Json<Value> {
    crate::routes_notify::queue(&s.pool, body)
}

async fn list_notifications(State(s): State<Arc<OrgState>>) -> Json<Value> {
    crate::routes_notify::list_pending(&s.pool)
}

// --- Decisions (decision_log table) ---

async fn log_decision(
    State(s): State<Arc<OrgState>>,
    Json(body): Json<crate::routes_decisions::DecisionBody>,
) -> Json<Value> {
    crate::routes_decisions::log(&s.pool, body)
}

#[derive(Deserialize)]
pub struct DecisionQuery {
    pub plan_id: Option<i64>,
    pub task_id: Option<i64>,
    pub agent: Option<String>,
    pub limit: Option<u32>,
}

async fn query_decisions(
    State(s): State<Arc<OrgState>>,
    Query(q): Query<DecisionQuery>,
) -> Json<Value> {
    crate::routes_decisions::query(&s.pool, q)
}
