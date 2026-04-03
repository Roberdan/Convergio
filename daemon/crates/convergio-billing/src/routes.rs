//! HTTP API routes for billing.
//!
//! - GET  /api/billing/usage    — usage summary for org/agent
//! - GET  /api/billing/invoices — list invoices for org
//! - GET  /api/billing/rates    — rate cards for org
//! - POST /api/billing/alerts   — configure alert thresholds

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::{Deserialize, Serialize};

use convergio_db::pool::ConnPool;

use crate::types::{BudgetConfig, BudgetScope, CostAlert, Invoice, RateCard};
use crate::{alerts, invoices, metering, rates};

/// Shared state for billing routes.
pub struct BillingState {
    pub pool: ConnPool,
}

/// Build the billing API router.
pub fn billing_routes(state: Arc<BillingState>) -> Router {
    Router::new()
        .route("/api/billing/usage", get(handle_usage))
        .route("/api/billing/invoices", get(handle_invoices))
        .route("/api/billing/rates", get(handle_rates))
        .route("/api/billing/alerts", post(handle_alerts))
        .with_state(state)
}

#[derive(Debug, Deserialize)]
pub struct UsageQuery {
    pub org_id: String,
    pub from: Option<String>,
    pub to: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct UsageResponse {
    pub org_id: String,
    pub daily_cost: f64,
    pub monthly_cost: f64,
    pub categories: Vec<CategoryBreakdown>,
}

#[derive(Debug, Serialize)]
pub struct CategoryBreakdown {
    pub category: String,
    pub quantity: f64,
    pub cost: f64,
}

async fn handle_usage(
    State(state): State<Arc<BillingState>>,
    Query(params): Query<UsageQuery>,
) -> Json<UsageResponse> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => {
            return Json(UsageResponse {
                org_id: params.org_id,
                daily_cost: 0.0,
                monthly_cost: 0.0,
                categories: vec![],
            })
        }
    };

    let daily = metering::org_cost_today(&conn, &params.org_id).unwrap_or(0.0);
    let monthly = metering::org_cost_month(&conn, &params.org_id).unwrap_or(0.0);
    let from = params.from.as_deref().unwrap_or("2020-01-01");
    let to = params.to.as_deref().unwrap_or("2099-12-31");
    let cats = metering::usage_by_category(&conn, &params.org_id, from, to)
        .unwrap_or_default()
        .into_iter()
        .map(|(cat, qty, cost)| CategoryBreakdown {
            category: cat,
            quantity: qty,
            cost,
        })
        .collect();

    Json(UsageResponse {
        org_id: params.org_id,
        daily_cost: daily,
        monthly_cost: monthly,
        categories: cats,
    })
}

#[derive(Debug, Deserialize)]
pub struct InvoicesQuery {
    pub org_id: String,
}

async fn handle_invoices(
    State(state): State<Arc<BillingState>>,
    Query(params): Query<InvoicesQuery>,
) -> Json<Vec<Invoice>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    Json(invoices::list_invoices(&conn, &params.org_id).unwrap_or_default())
}

#[derive(Debug, Deserialize)]
pub struct RatesQuery {
    pub org_id: String,
}

async fn handle_rates(
    State(state): State<Arc<BillingState>>,
    Query(params): Query<RatesQuery>,
) -> Json<Vec<RateCard>> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(_) => return Json(vec![]),
    };
    Json(rates::get_rates(&conn, &params.org_id).unwrap_or_default())
}

#[derive(Debug, Deserialize)]
pub struct AlertRequest {
    pub entity_id: String,
    pub scope: String,
    pub daily_limit_usd: f64,
    pub monthly_limit_usd: f64,
    pub auto_pause: bool,
}

async fn handle_alerts(
    State(state): State<Arc<BillingState>>,
    Json(body): Json<AlertRequest>,
) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": {"code": "POOL_ERROR", "message": e.to_string()}
            }))
        }
    };

    let scope = match body.scope.as_str() {
        "platform" => BudgetScope::Platform,
        "agent" => BudgetScope::Agent,
        _ => BudgetScope::Org,
    };

    let config = BudgetConfig {
        scope,
        entity_id: body.entity_id.clone(),
        daily_limit_usd: body.daily_limit_usd,
        monthly_limit_usd: body.monthly_limit_usd,
        auto_pause: body.auto_pause,
    };

    if let Err(e) = crate::budget::set_budget(&conn, &config) {
        return Json(serde_json::json!({
            "error": {"code": "DB_ERROR", "message": e.to_string()}
        }));
    }

    let alert: Option<CostAlert> = alerts::check_thresholds(&conn, &body.entity_id).unwrap_or(None);

    Json(serde_json::json!({
        "status": "configured",
        "entity_id": body.entity_id,
        "alert": alert,
    }))
}
