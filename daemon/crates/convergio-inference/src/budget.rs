//! Budget-aware token tracking per agent/org/plan.
//!
//! Persists cost records in SQLite and provides real-time aggregation.
//! Supports budget limits per agent and per org, with automatic tier downgrade
//! when budget is nearly exhausted.

use rusqlite::Connection;
use serde::{Deserialize, Serialize};

use crate::types::{CostRecord, CostSummary, InferenceTier};

/// Budget configuration for an entity (agent or org).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetConfig {
    /// Daily token budget.
    pub daily_token_limit: u64,
    /// Daily cost budget in USD.
    pub daily_cost_limit_usd: f64,
    /// Threshold (0.0-1.0) at which to start downgrading tiers.
    pub downgrade_threshold: f64,
}

impl Default for BudgetConfig {
    fn default() -> Self {
        Self {
            daily_token_limit: 10_000_000,
            daily_cost_limit_usd: 50.0,
            downgrade_threshold: 0.8,
        }
    }
}

/// Record a cost entry in the database.
pub fn record_cost(conn: &Connection, record: &CostRecord) -> Result<(), String> {
    conn.execute(
        "INSERT INTO inference_costs (agent_id, org_id, plan_id, model,
         tokens_input, tokens_output, cost_usd, created_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        rusqlite::params![
            record.agent_id,
            record.org_id,
            record.plan_id,
            record.model,
            record.tokens_input,
            record.tokens_output,
            record.cost_usd,
            record.timestamp,
        ],
    )
    .map_err(|e| format!("failed to record cost: {e}"))?;
    Ok(())
}

/// Get cost summary for an agent (today).
pub fn agent_costs_today(conn: &Connection, agent_id: &str) -> Result<CostSummary, String> {
    costs_by_scope(conn, "agent_id", agent_id)
}

/// Get cost summary for an org (today).
pub fn org_costs_today(conn: &Connection, org_id: &str) -> Result<CostSummary, String> {
    costs_by_scope(conn, "org_id", org_id)
}

/// Get cost summary for a plan (lifetime).
pub fn plan_costs(conn: &Connection, plan_id: i64) -> Result<CostSummary, String> {
    let sql = "SELECT COALESCE(SUM(tokens_input + tokens_output), 0),
                      COALESCE(SUM(cost_usd), 0.0),
                      COUNT(*)
               FROM inference_costs WHERE plan_id = ?1";

    let (total_tokens, total_cost, count): (u64, f64, u64) = conn
        .query_row(sql, [plan_id], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))
        .map_err(|e| format!("query error: {e}"))?;

    let models = distinct_models_for_plan(conn, plan_id)?;

    Ok(CostSummary {
        scope: "plan".into(),
        scope_id: plan_id.to_string(),
        total_tokens,
        total_cost_usd: total_cost,
        request_count: count,
        models_used: models,
    })
}

/// Check if an agent should be downgraded based on budget usage.
pub fn should_downgrade(
    conn: &Connection,
    agent_id: &str,
    config: &BudgetConfig,
) -> Result<bool, String> {
    let summary = agent_costs_today(conn, agent_id)?;
    let cost_ratio = summary.total_cost_usd / config.daily_cost_limit_usd;
    let token_ratio = summary.total_tokens as f64 / config.daily_token_limit as f64;
    Ok(cost_ratio >= config.downgrade_threshold || token_ratio >= config.downgrade_threshold)
}

/// Downgrade a tier by one step; floor is T1Trivial.
pub fn downgrade_tier(tier: InferenceTier) -> InferenceTier {
    match tier {
        InferenceTier::T1Trivial => InferenceTier::T1Trivial,
        InferenceTier::T2Standard => InferenceTier::T1Trivial,
        InferenceTier::T3Complex => InferenceTier::T2Standard,
        InferenceTier::T4Critical => InferenceTier::T3Complex,
    }
}

// --- internal helpers ---

fn costs_by_scope(conn: &Connection, col: &str, val: &str) -> Result<CostSummary, String> {
    let sql = format!(
        "SELECT COALESCE(SUM(tokens_input + tokens_output), 0),
                COALESCE(SUM(cost_usd), 0.0),
                COUNT(*)
         FROM inference_costs
         WHERE {col} = ?1 AND date(created_at) = date('now')"
    );

    let (total_tokens, total_cost, count): (u64, f64, u64) = conn
        .query_row(&sql, [val], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))
        .map_err(|e| format!("query error: {e}"))?;

    Ok(CostSummary {
        scope: col.replace("_id", "").to_string(),
        scope_id: val.to_string(),
        total_tokens,
        total_cost_usd: total_cost,
        request_count: count,
        models_used: vec![],
    })
}

fn distinct_models_for_plan(conn: &Connection, plan_id: i64) -> Result<Vec<String>, String> {
    let mut stmt = conn
        .prepare("SELECT DISTINCT model FROM inference_costs WHERE plan_id = ?1")
        .map_err(|e| format!("prepare error: {e}"))?;
    let rows = stmt
        .query_map([plan_id], |r| r.get(0))
        .map_err(|e| format!("query error: {e}"))?;
    let mut models = Vec::new();
    for row in rows {
        models.push(row.map_err(|e| format!("row error: {e}"))?);
    }
    Ok(models)
}
