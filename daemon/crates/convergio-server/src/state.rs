//! Server state shared across all handlers.

use convergio_db::pool::ConnPool;
use convergio_telemetry::health::HealthRegistry;
use convergio_telemetry::metrics::MetricsCollector;
use convergio_types::config::ConvergioConfig;
use std::sync::{Arc, RwLock};

/// Shared state for the Axum router, injected into all handlers.
#[derive(Clone)]
pub struct ServerState {
    pool: ConnPool,
    pub config: Arc<RwLock<ConvergioConfig>>,
    pub health: Arc<HealthRegistry>,
    pub metrics: Arc<MetricsCollector>,
    pub dev_mode: bool,
}

impl ServerState {
    pub fn new(
        pool: ConnPool,
        config: Arc<RwLock<ConvergioConfig>>,
        health: Arc<HealthRegistry>,
        metrics: Arc<MetricsCollector>,
        dev_mode: bool,
    ) -> Self {
        Self { pool, config, health, metrics, dev_mode }
    }

    /// Get a pooled database connection.
    pub fn get_conn(
        &self,
    ) -> Result<r2d2::PooledConnection<r2d2_sqlite::SqliteConnectionManager>, r2d2::Error> {
        self.pool.get()
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }
}

/// Standardized API error response.
#[derive(Debug)]
pub enum ApiError {
    BadRequest(String),
    NotFound(String),
    Forbidden(String),
    RateLimited(String),
    Conflict(String),
    Internal(String),
}

impl ApiError {
    pub fn bad_request(msg: impl Into<String>) -> Self {
        Self::BadRequest(msg.into())
    }
    pub fn not_found(msg: impl Into<String>) -> Self {
        Self::NotFound(msg.into())
    }
    pub fn forbidden(msg: impl Into<String>) -> Self {
        Self::Forbidden(msg.into())
    }
    pub fn rate_limited(msg: impl Into<String>) -> Self {
        Self::RateLimited(msg.into())
    }
    pub fn internal(msg: impl Into<String>) -> Self {
        Self::Internal(msg.into())
    }
}

impl axum::response::IntoResponse for ApiError {
    fn into_response(self) -> axum::response::Response {
        use axum::http::StatusCode;
        use axum::Json;

        let (status, message) = match self {
            Self::BadRequest(m) => (StatusCode::BAD_REQUEST, m),
            Self::NotFound(m) => (StatusCode::NOT_FOUND, m),
            Self::Forbidden(m) => (StatusCode::FORBIDDEN, m),
            Self::RateLimited(m) => (StatusCode::TOO_MANY_REQUESTS, m),
            Self::Conflict(m) => (StatusCode::CONFLICT, m),
            Self::Internal(m) => (StatusCode::INTERNAL_SERVER_ERROR, m),
        };
        let request_id = uuid::Uuid::new_v4().to_string();
        let body = serde_json::json!({
            "error": {
                "code": status.as_u16(),
                "message": message,
                "request_id": request_id,
                "timestamp": chrono::Utc::now().to_rfc3339(),
            }
        });
        (status, Json(body)).into_response()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn api_error_variants() {
        let _ = ApiError::bad_request("test");
        let _ = ApiError::not_found("test");
        let _ = ApiError::forbidden("test");
        let _ = ApiError::rate_limited("test");
        let _ = ApiError::internal("test");
    }
}
