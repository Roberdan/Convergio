//! Scoped tokens for org-level access control.
//!
//! Each installed org gets a token with explicit permissions, budget
//! limits, and expiry. Tokens are validated before any org operation.

use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

/// Scoped permissions for an org token.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgTokenPermissions {
    /// IPC channels the org can publish to.
    pub ipc_publish: Vec<String>,
    /// IPC channels the org can subscribe to.
    pub ipc_subscribe: Vec<String>,
    /// API route prefixes the org can serve.
    pub routes: Vec<String>,
    /// Whether the org can delegate tasks.
    pub can_delegate: bool,
    /// Whether the org can receive delegated tasks.
    pub can_receive: bool,
}

/// Budget limits embedded in the token.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgTokenBudget {
    pub max_api_calls_per_hour: u64,
    pub max_tokens_per_day: u64,
    pub max_compute_seconds: u64,
}

/// Claims embedded in a scoped org token.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgTokenClaims {
    /// Org package name (subject).
    pub sub: String,
    /// Org version at install time.
    pub version: String,
    /// Granted permissions.
    pub permissions: OrgTokenPermissions,
    /// Budget hardcap.
    pub budget: OrgTokenBudget,
    /// Issued-at timestamp (Unix seconds).
    pub iat: u64,
    /// Expiry timestamp (Unix seconds).
    pub exp: u64,
}

/// Token validation errors.
#[derive(Debug, thiserror::Error)]
pub enum TokenError {
    #[error("token expired")]
    Expired,
    #[error("permission denied: {0}")]
    PermissionDenied(String),
    #[error("budget exceeded: {0}")]
    BudgetExceeded(String),
}

/// Create org token claims from manifest data.
pub fn create_org_claims(
    org_name: &str,
    version: &str,
    permissions: OrgTokenPermissions,
    budget: OrgTokenBudget,
    ttl_secs: u64,
) -> OrgTokenClaims {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    OrgTokenClaims {
        sub: org_name.to_string(),
        version: version.to_string(),
        permissions,
        budget,
        iat: now,
        exp: now + ttl_secs,
    }
}

/// Validate token is not expired.
pub fn validate_expiry(claims: &OrgTokenClaims) -> Result<(), TokenError> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    if now > claims.exp {
        return Err(TokenError::Expired);
    }
    Ok(())
}

/// Check if org has permission to publish to a channel.
pub fn check_ipc_publish(claims: &OrgTokenClaims, channel: &str) -> Result<(), TokenError> {
    let prefixed = format!("org.{}.{}", claims.sub, channel);
    let allowed = claims
        .permissions
        .ipc_publish
        .iter()
        .any(|c| c == channel || c == &prefixed || c == "*");
    if allowed {
        Ok(())
    } else {
        Err(TokenError::PermissionDenied(format!(
            "org '{}' cannot publish to '{channel}'",
            claims.sub
        )))
    }
}

/// Check if org has permission to subscribe to a channel.
pub fn check_ipc_subscribe(claims: &OrgTokenClaims, channel: &str) -> Result<(), TokenError> {
    let prefixed = format!("org.{}.{}", claims.sub, channel);
    let allowed = claims
        .permissions
        .ipc_subscribe
        .iter()
        .any(|c| c == channel || c == &prefixed || c == "*");
    if allowed {
        Ok(())
    } else {
        Err(TokenError::PermissionDenied(format!(
            "org '{}' cannot subscribe to '{channel}'",
            claims.sub
        )))
    }
}

/// Check if budget allows an API call (simple counter check).
pub fn check_budget(claims: &OrgTokenClaims, current_calls: u64) -> Result<(), TokenError> {
    if current_calls >= claims.budget.max_api_calls_per_hour {
        return Err(TokenError::BudgetExceeded(format!(
            "org '{}' exceeded {} calls/hour",
            claims.sub, claims.budget.max_api_calls_per_hour
        )));
    }
    Ok(())
}

#[cfg(test)]
#[path = "token_tests.rs"]
mod tests;
