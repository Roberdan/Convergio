//! API routes: GET /api/inference/costs, GET /api/inference/routing-decision.

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::get;
use axum::Router;
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;

use crate::budget;
use crate::metrics::{MetricsCollector, TimeWindow};
use crate::router::ModelRouter;
use crate::types::{
    CostSummary, InferenceConstraints, InferenceRequest, InferenceTier, RoutingDecision,
};
use convergio_db::pool::ConnPool;

/// Shared state for inference routes.
pub struct InferenceState {
    pub pool: ConnPool,
    pub router: Arc<RwLock<ModelRouter>>,
    pub metrics: Arc<RwLock<MetricsCollector>>,
}

/// Query params for GET /costs.
#[derive(Debug, Deserialize)]
pub struct CostsQuery {
    pub agent_id: Option<String>,
    pub org_id: Option<String>,
    pub plan_id: Option<i64>,
}

/// Response for GET /costs.
#[derive(Debug, Serialize)]
pub struct CostsResponse {
    pub summaries: Vec<CostSummary>,
}

/// Query params for GET /routing-decision.
#[derive(Debug, Deserialize)]
pub struct RoutingQuery {
    pub prompt: Option<String>,
    pub tier: Option<String>,
    pub agent_id: Option<String>,
    pub max_cost: Option<f64>,
}

/// Response for GET /routing-decision.
#[derive(Debug, Serialize)]
pub struct RoutingResponse {
    pub decision: RoutingDecision,
    pub model_metrics: Vec<crate::metrics::ModelMetrics>,
}

/// Build the inference API router.
pub fn inference_routes(state: Arc<InferenceState>) -> Router {
    Router::new()
        .route("/api/inference/costs", get(handle_costs))
        .route("/api/inference/routing-decision", get(handle_routing))
        .with_state(state)
}

async fn handle_costs(
    State(state): State<Arc<InferenceState>>,
    Query(params): Query<CostsQuery>,
) -> Json<CostsResponse> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(CostsResponse { summaries: vec![] }),
    };

    let mut summaries = Vec::new();

    if let Some(agent_id) = &params.agent_id {
        if let Ok(s) = budget::agent_costs_today(&conn, agent_id) {
            summaries.push(s);
        }
    }
    if let Some(org_id) = &params.org_id {
        if let Ok(s) = budget::org_costs_today(&conn, org_id) {
            summaries.push(s);
        }
    }
    if let Some(plan_id) = params.plan_id {
        if let Ok(s) = budget::plan_costs(&conn, plan_id) {
            summaries.push(s);
        }
    }

    Json(CostsResponse { summaries })
}

async fn handle_routing(
    State(state): State<Arc<InferenceState>>,
    Query(params): Query<RoutingQuery>,
) -> Json<serde_json::Value> {
    let tier_hint = params.tier.as_deref().and_then(InferenceTier::from_label);

    let request = InferenceRequest {
        prompt: params.prompt.unwrap_or_default(),
        max_tokens: 256,
        tier_hint,
        agent_id: params.agent_id.clone().unwrap_or_else(|| "anonymous".into()),
        org_id: None,
        plan_id: None,
        constraints: InferenceConstraints {
            max_latency_ms: None,
            max_cost: params.max_cost,
        },
    };

    // Check budget for downgrade
    let should_downgrade = if let Some(agent_id) = &params.agent_id {
        let conn = state.pool.get().ok();
        conn.map(|c| {
            budget::should_downgrade(&c, agent_id, &budget::BudgetConfig::default())
                .unwrap_or(false)
        })
        .unwrap_or(false)
    } else {
        false
    };

    let router = state.router.read().await;
    match router.route(&request, should_downgrade) {
        Ok((_resp, decision)) => {
            let metrics_lock = state.metrics.read().await;
            let model_metrics = metrics_lock.all_metrics(TimeWindow::OneHour);
            Json(serde_json::json!({
                "decision": decision,
                "model_metrics": model_metrics,
            }))
        }
        Err(e) => Json(serde_json::json!({
            "error": { "code": "NO_MODEL", "message": e }
        })),
    }
}
