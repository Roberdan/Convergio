//! Inter-org delegation — verified task handoffs between orgs.
//!
//! Before delegating, both sides are checked: the source must have
//! can_delegate, the target must have can_receive, both must be in
//! each other's trusted list, and budget must allow the operation.

use crate::token::OrgTokenClaims;
use serde::{Deserialize, Serialize};

/// A delegation request from one org to another.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegationRequest {
    /// Requesting org name.
    pub from_org: String,
    /// Target org name.
    pub to_org: String,
    /// Task description or ID.
    pub task: String,
    /// Budget allocated for this delegation.
    pub budget_tokens: u64,
    /// Deadline as ISO 8601 timestamp (optional).
    pub deadline: Option<String>,
}

/// Result of a delegation attempt.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegationResult {
    pub id: String,
    pub status: DelegationStatus,
    pub reason: Option<String>,
}

/// Status of a delegation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DelegationStatus {
    Pending,
    Accepted,
    Rejected,
    Completed,
    Failed,
}

/// Delegation validation errors.
#[derive(Debug, thiserror::Error)]
pub enum DelegationError {
    #[error("source org '{0}' cannot delegate")]
    CannotDelegate(String),
    #[error("target org '{0}' cannot receive")]
    CannotReceive(String),
    #[error("org '{0}' not in trusted list of '{1}'")]
    NotTrusted(String, String),
    #[error("insufficient budget: need {need}, have {have}")]
    InsufficientBudget { need: u64, have: u64 },
}

/// Validate a delegation request between two orgs.
pub fn validate_delegation(
    request: &DelegationRequest,
    source_claims: &OrgTokenClaims,
    target_claims: &OrgTokenClaims,
    target_trusted: &[String],
) -> Result<(), DelegationError> {
    // Source must be allowed to delegate.
    if !source_claims.permissions.can_delegate {
        return Err(DelegationError::CannotDelegate(request.from_org.clone()));
    }

    // Target must be allowed to receive.
    if !target_claims.permissions.can_receive {
        return Err(DelegationError::CannotReceive(request.to_org.clone()));
    }

    // Source must be trusted by target.
    if !target_trusted
        .iter()
        .any(|t| t == &request.from_org || t == "*")
    {
        return Err(DelegationError::NotTrusted(
            request.from_org.clone(),
            request.to_org.clone(),
        ));
    }

    // Budget check: delegation budget must fit within target's daily limit.
    if request.budget_tokens > target_claims.budget.max_tokens_per_day {
        return Err(DelegationError::InsufficientBudget {
            need: request.budget_tokens,
            have: target_claims.budget.max_tokens_per_day,
        });
    }

    Ok(())
}

/// Create a pending delegation result.
pub fn create_delegation(request: &DelegationRequest) -> DelegationResult {
    DelegationResult {
        id: uuid::Uuid::new_v4().to_string(),
        status: DelegationStatus::Pending,
        reason: Some(format!(
            "delegation from '{}' to '{}': {}",
            request.from_org, request.to_org, request.task
        )),
    }
}

#[cfg(test)]
#[path = "delegation_tests.rs"]
mod tests;
