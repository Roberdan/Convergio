//! Shared error types used across the platform.

/// Top-level error type for the Convergio platform.
#[derive(Debug, thiserror::Error)]
pub enum ConvergioError {
    #[error("database error: {0}")]
    Db(String),

    #[error("extension error: {module} — {message}")]
    Extension { module: String, message: String },

    #[error("dependency not satisfied: {capability} required by {requirer}")]
    DependencyMissing { capability: String, requirer: String },

    #[error("permission denied: {0}")]
    PermissionDenied(String),

    #[error("not found: {0}")]
    NotFound(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("budget exceeded: {org} spent {spent:.2} of {limit:.2} USD")]
    BudgetExceeded { org: String, spent: f64, limit: f64 },

    #[error("{0}")]
    Internal(String),
}
