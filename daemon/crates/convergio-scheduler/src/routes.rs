//! HTTP API routes for the scheduler.
//!
//! - POST /api/scheduler/decide   — make a scheduling decision
//! - GET  /api/scheduler/policy   — get current policy
//! - POST /api/scheduler/policy   — update policy weights
//! - GET  /api/scheduler/history  — list recent decisions

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use rusqlite::params;
use serde::Deserialize;

use convergio_db::pool::ConnPool;

use crate::policy;
use crate::types::{SchedulerPolicy, SchedulingDecision, SchedulingRequest};

/// Shared state for scheduler routes.
pub struct SchedulerState {
    pub pool: ConnPool,
}

/// Build the scheduler API router.
pub fn scheduler_routes(state: Arc<SchedulerState>) -> Router {
    Router::new()
        .route("/api/scheduler/decide", post(handle_decide))
        .route(
            "/api/scheduler/policy",
            get(handle_get_policy).post(handle_set_policy),
        )
        .route("/api/scheduler/history", get(handle_history))
        .with_state(state)
}

/// POST /api/scheduler/decide — score peers and assign best.
async fn handle_decide(
    State(state): State<Arc<SchedulerState>>,
    Json(req): Json<SchedulingRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": {"code": "POOL_ERROR", "message": e.to_string()}
            }))
        }
    };

    let pol = policy::load_policy(&conn, "default");

    // Query available peers from node_capabilities table.
    let peers = load_peer_capabilities(&conn);
    if peers.is_empty() {
        return Json(serde_json::json!({
            "error": {"code": "NO_PEERS", "message": "no peers with capabilities found"}
        }));
    }

    let candidates: Vec<_> = peers
        .iter()
        .map(|(name, caps)| policy::score_peer(name, caps, 0.0, &req, &pol))
        .collect();

    let best = match policy::select_best(candidates.clone()) {
        Some(b) => b,
        None => {
            return Json(serde_json::json!({
                "error": {"code": "NO_MATCH", "message": "no suitable peer found"}
            }))
        }
    };

    let tier = req.tier_hint.clone().unwrap_or_else(|| "t2".into());
    let decision = SchedulingDecision {
        task_id: req.task_id,
        assigned_peer: best.peer_name.clone(),
        assigned_tier: tier.clone(),
        estimated_cost: best.cost_score * req.max_cost_usd.unwrap_or(0.1),
        reason: format!(
            "score {:.3}, caps {:.0}%",
            best.score,
            best.capabilities_match * 100.0
        ),
        alternatives: candidates
            .into_iter()
            .filter(|c| c.peer_name != best.peer_name)
            .collect(),
    };

    // Persist decision to history.
    let _ = conn.execute(
        "INSERT INTO scheduling_decisions (task_id, plan_id, assigned_peer, \
         assigned_tier, estimated_cost, reason) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![
            decision.task_id,
            req.plan_id,
            decision.assigned_peer,
            decision.assigned_tier,
            decision.estimated_cost,
            decision.reason,
        ],
    );

    Json(serde_json::to_value(&decision).unwrap_or_default())
}

/// GET /api/scheduler/policy
async fn handle_get_policy(State(state): State<Arc<SchedulerState>>) -> Json<SchedulerPolicy> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(policy::default_policy()),
    };
    Json(policy::load_policy(&conn, "default"))
}

/// POST /api/scheduler/policy — update weights.
async fn handle_set_policy(
    State(state): State<Arc<SchedulerState>>,
    Json(body): Json<SchedulerPolicy>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": {"code": "POOL_ERROR", "message": e.to_string()}
            }))
        }
    };
    if let Err(e) = policy::save_policy(&conn, &body) {
        return Json(serde_json::json!({
            "error": {"code": "DB_ERROR", "message": e.to_string()}
        }));
    }
    Json(serde_json::json!({"status": "updated", "name": body.name}))
}

#[derive(Debug, Deserialize)]
pub struct HistoryQuery {
    pub limit: Option<i64>,
}

/// GET /api/scheduler/history — recent scheduling decisions.
async fn handle_history(
    State(state): State<Arc<SchedulerState>>,
    Query(params): Query<HistoryQuery>,
) -> Json<Vec<SchedulingDecision>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    let limit = params.limit.unwrap_or(20).min(100);
    let mut stmt = match conn.prepare(
        "SELECT task_id, assigned_peer, assigned_tier, estimated_cost, reason \
         FROM scheduling_decisions ORDER BY decided_at DESC LIMIT ?1",
    ) {
        Ok(s) => s,
        Err(_) => return Json(vec![]),
    };
    let rows = match stmt.query_map(params![limit], |row| {
        Ok(SchedulingDecision {
            task_id: row.get(0)?,
            assigned_peer: row.get(1)?,
            assigned_tier: row.get(2)?,
            estimated_cost: row.get(3)?,
            reason: row.get(4)?,
            alternatives: vec![],
        })
    }) {
        Ok(r) => r.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(rows)
}

/// Load peer names and their capability names from node_capabilities.
fn load_peer_capabilities(conn: &rusqlite::Connection) -> Vec<(String, Vec<String>)> {
    let mut stmt = match conn.prepare(
        "SELECT peer_name, capability_name FROM node_capabilities \
         ORDER BY peer_name",
    ) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    let rows: Vec<(String, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))
        .unwrap_or_else(|_| panic!("query failed"))
        .filter_map(|r| r.ok())
        .collect();
    let mut map: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();
    for (peer, cap) in rows {
        map.entry(peer).or_default().push(cap);
    }
    map.into_iter().collect()
}
