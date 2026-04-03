//! Sandbox runtime — isolation for installed org packages.
//!
//! Each org gets: DB table prefix, route prefix, IPC channel prefix,
//! and budget hardcap enforcement. Sandbox violations are blocked
//! and recorded.

use crate::manifest::OrgManifest;
use serde::{Deserialize, Serialize};

/// Runtime sandbox configuration for an installed org.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgSandbox {
    /// Org package name.
    pub org_name: String,
    /// DB table prefix (e.g. "org_legal_corp_").
    pub db_prefix: String,
    /// Route prefix (e.g. "/org/legal-corp").
    pub route_prefix: String,
    /// IPC channel prefix (e.g. "org.legal-corp.").
    pub ipc_prefix: String,
    /// Budget hardcap: max API calls per hour.
    pub budget_api_calls: u64,
    /// Budget hardcap: max tokens per day.
    pub budget_tokens_day: u64,
    /// Budget hardcap: max compute seconds.
    pub budget_compute_secs: u64,
}

/// Sandbox enforcement errors.
#[derive(Debug, thiserror::Error)]
pub enum SandboxError {
    #[error("DB table violation: '{0}' does not start with prefix '{1}'")]
    DbPrefixViolation(String, String),
    #[error("route violation: '{0}' outside prefix '{1}'")]
    RoutePrefixViolation(String, String),
    #[error("IPC channel violation: '{0}' outside prefix '{1}'")]
    IpcPrefixViolation(String, String),
    #[error("budget exceeded: {0}")]
    BudgetExceeded(String),
}

/// Create a sandbox from an installed org manifest.
pub fn create_sandbox(manifest: &OrgManifest) -> OrgSandbox {
    let name = &manifest.package.name;
    let db_safe = name.replace('-', "_");
    OrgSandbox {
        org_name: name.clone(),
        db_prefix: format!("org_{db_safe}_"),
        route_prefix: format!("/org/{name}"),
        ipc_prefix: format!("org.{name}."),
        budget_api_calls: manifest.budget.max_api_calls_per_hour,
        budget_tokens_day: manifest.budget.max_tokens_per_day,
        budget_compute_secs: manifest.budget.max_compute_seconds,
    }
}

/// Validate a DB table name is within the org sandbox.
pub fn check_db_table(sandbox: &OrgSandbox, table_name: &str) -> Result<(), SandboxError> {
    if table_name.starts_with(&sandbox.db_prefix) {
        Ok(())
    } else {
        Err(SandboxError::DbPrefixViolation(
            table_name.into(),
            sandbox.db_prefix.clone(),
        ))
    }
}

/// Validate a route path is within the org sandbox.
pub fn check_route(sandbox: &OrgSandbox, path: &str) -> Result<(), SandboxError> {
    if path.starts_with(&sandbox.route_prefix) {
        Ok(())
    } else {
        Err(SandboxError::RoutePrefixViolation(
            path.into(),
            sandbox.route_prefix.clone(),
        ))
    }
}

/// Validate an IPC channel is within the org sandbox.
pub fn check_ipc_channel(sandbox: &OrgSandbox, channel: &str) -> Result<(), SandboxError> {
    if channel.starts_with(&sandbox.ipc_prefix) {
        Ok(())
    } else {
        Err(SandboxError::IpcPrefixViolation(
            channel.into(),
            sandbox.ipc_prefix.clone(),
        ))
    }
}

/// Check if budget allows the operation.
pub fn check_budget_limit(sandbox: &OrgSandbox, current_calls: u64) -> Result<(), SandboxError> {
    if current_calls >= sandbox.budget_api_calls {
        Err(SandboxError::BudgetExceeded(format!(
            "org '{}' exceeded {} calls/hour limit",
            sandbox.org_name, sandbox.budget_api_calls
        )))
    } else {
        Ok(())
    }
}

/// Prefix a SQL migration so all tables are namespaced.
pub fn prefix_migration_sql(sandbox: &OrgSandbox, sql: &str) -> String {
    // Handle "IF NOT EXISTS" variant first to avoid partial matches.
    let result = sql.replace(
        "CREATE TABLE IF NOT EXISTS ",
        &format!("CREATE TABLE IF NOT EXISTS {}", sandbox.db_prefix),
    );
    // Handle plain "CREATE TABLE " only for lines not already prefixed.
    result
        .lines()
        .map(|line| {
            if line.contains("IF NOT EXISTS") {
                line.to_string()
            } else {
                line.replace(
                    "CREATE TABLE ",
                    &format!("CREATE TABLE {}", sandbox.db_prefix),
                )
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

#[cfg(test)]
#[path = "sandbox_tests.rs"]
mod tests;
