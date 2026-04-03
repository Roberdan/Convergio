//! Core types for billing, metering, and inter-org economics.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Category of a metered action.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ActionCategory {
    ApiCall,
    TokenInference,
    ComputeTime,
    Storage,
}

/// A single metered usage record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageRecord {
    pub id: Option<i64>,
    pub org_id: String,
    pub agent_id: Option<String>,
    pub task_id: Option<i64>,
    pub category: ActionCategory,
    pub quantity: f64,
    pub unit: String,
    pub cost_usd: f64,
    pub model: Option<String>,
    pub created_at: DateTime<Utc>,
}

/// Budget scope: platform, org, or agent level.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum BudgetScope {
    Platform,
    Org,
    Agent,
}

/// A budget configuration entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetConfig {
    pub scope: BudgetScope,
    pub entity_id: String,
    pub daily_limit_usd: f64,
    pub monthly_limit_usd: f64,
    pub auto_pause: bool,
}

/// Budget status with spending info.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetStatus {
    pub entity_id: String,
    pub scope: BudgetScope,
    pub daily_limit: f64,
    pub monthly_limit: f64,
    pub daily_spent: f64,
    pub monthly_spent: f64,
    pub daily_pct: f64,
    pub monthly_pct: f64,
    pub auto_pause: bool,
    pub paused: bool,
}

/// A rate card entry — pricing declared by an org for a capability.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RateCard {
    pub id: Option<i64>,
    pub org_id: String,
    pub capability: String,
    pub price_per_unit: f64,
    pub unit: String,
    pub effective_from: String,
}

/// An invoice line item.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InvoiceItem {
    pub category: String,
    pub quantity: f64,
    pub unit_price: f64,
    pub total: f64,
    pub description: String,
}

/// A generated invoice for an org.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Invoice {
    pub id: Option<i64>,
    pub org_id: String,
    pub period_start: String,
    pub period_end: String,
    pub items: Vec<InvoiceItem>,
    pub total_usd: f64,
    pub created_at: DateTime<Utc>,
}

/// Alert severity level.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AlertLevel {
    Warning,
    High,
    Critical,
}

/// A cost alert triggered by threshold breach.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostAlert {
    pub entity_id: String,
    pub scope: BudgetScope,
    pub level: AlertLevel,
    pub usage_pct: f64,
    pub message: String,
    pub auto_paused: bool,
}

/// Settlement record — log-only for now.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SettlementRecord {
    pub id: Option<i64>,
    pub from_org: String,
    pub to_org: String,
    pub amount_usd: f64,
    pub capability: String,
    pub reference_task: Option<i64>,
    pub created_at: DateTime<Utc>,
}

/// Tamper-evident audit entry with hash chain.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    pub id: Option<i64>,
    pub event_type: String,
    pub entity_id: String,
    pub amount_usd: f64,
    pub details: String,
    pub prev_hash: String,
    pub hash: String,
    pub created_at: DateTime<Utc>,
}

/// Free tier / quota configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Quota {
    pub org_id: String,
    pub daily_free_usd: f64,
    pub monthly_free_usd: f64,
}

impl std::fmt::Display for ActionCategory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ApiCall => write!(f, "api_call"),
            Self::TokenInference => write!(f, "token_inference"),
            Self::ComputeTime => write!(f, "compute_time"),
            Self::Storage => write!(f, "storage"),
        }
    }
}

impl ActionCategory {
    pub fn from_str_value(s: &str) -> Self {
        match s {
            "api_call" => Self::ApiCall,
            "token_inference" => Self::TokenInference,
            "compute_time" => Self::ComputeTime,
            "storage" => Self::Storage,
            _ => Self::ApiCall,
        }
    }
}
