use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error)]
pub enum IpcError {
    #[error("database: {0}")]
    Db(#[from] rusqlite::Error),
    #[error("pool: {0}")]
    Pool(#[from] r2d2::Error),
    #[error("rate limited: {0}")]
    RateLimited(String),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("http: {0}")]
    Http(String),
}

pub type IpcResult<T> = Result<T, IpcError>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInfo {
    pub name: String,
    pub host: String,
    pub agent_type: String,
    pub pid: Option<u32>,
    pub last_seen: String,
    pub parent_agent: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageInfo {
    pub id: String,
    pub from_agent: String,
    pub to_agent: Option<String>,
    pub channel: Option<String>,
    pub content: String,
    pub msg_type: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChannelInfo {
    pub name: String,
    pub description: Option<String>,
    pub created_by: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextEntry {
    pub key: String,
    pub value: String,
    pub version: i64,
    pub set_by: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSkill {
    pub agent: String,
    pub host: String,
    pub skill: String,
    pub confidence: f64,
    pub last_used: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelEntry {
    pub host: String,
    pub provider: String,
    pub model: String,
    pub size_gb: f64,
    pub quantization: String,
    pub last_seen: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeCapabilities {
    pub host: String,
    pub provider: String,
    pub models: Vec<String>,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subscription {
    pub name: String,
    pub provider: String,
    pub plan: String,
    pub budget_usd: f64,
    pub reset_day: i32,
    pub models: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BudgetEntry {
    pub subscription: String,
    pub date: String,
    pub tokens_in: i64,
    pub tokens_out: i64,
    pub estimated_cost_usd: f64,
    pub model: String,
    pub task_ref: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct BudgetStatus {
    pub subscription: String,
    pub budget_usd: f64,
    pub total_spent: f64,
    pub remaining_budget: f64,
    pub days_remaining: i32,
    pub daily_avg: f64,
    pub projected_total: f64,
    pub usage_pct: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct BudgetAlert {
    pub subscription: String,
    pub level: AlertLevel,
    pub usage_pct: f64,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, PartialEq)]
pub enum AlertLevel {
    Warning,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize)]
pub struct IpcStats {
    pub agents: u64,
    pub messages: u64,
    pub channels: u64,
    pub context_keys: u64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FileLock {
    pub file_path: String,
    pub locked_by: String,
    pub host: String,
    pub pid: i64,
    pub locked_at: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AcquireResult {
    Acquired,
    Rejected(FileLock),
}
