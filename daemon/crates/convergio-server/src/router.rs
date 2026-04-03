//! Router builder — wires extensions, applies middleware stack.
//!
//! All routes are `Router<()>`. ServerState is injected via tower
//! `Extension` layer so extension routes and system routes compose freely.

use crate::middleware_telemetry::telemetry_layer;
use crate::rate_limiter::{endpoint_category, RateLimiter};
use crate::state::ServerState;
use axum::body::Body;
use axum::http::{Method, Request, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use convergio_types::extension::{AppContext, Extension};
use std::sync::Arc;
use std::time::Duration;
use tower_http::compression::CompressionLayer;
use tower_http::limit::RequestBodyLimitLayer;
use tower_http::timeout::TimeoutLayer;

/// Build the full Axum router: system routes + extension routes + middleware.
pub fn build_router(
    state: ServerState,
    extensions: &[Arc<dyn Extension>],
    ctx: &AppContext,
) -> Router {
    let mut app = Router::new();

    // System routes
    app = app
        .route("/api/health", get(health_handler))
        .route("/api/telemetry", get(telemetry_handler))
        .route("/api/health/deep", get(deep_health_handler))
        .route("/api/metrics", get(metrics_handler));

    // Merge extension routes (all Router<()>)
    for ext in extensions {
        if let Some(ext_router) = ext.routes(ctx) {
            app = app.merge(ext_router);
        }
    }

    // Middleware stack (first registered = outermost = last to execute)
    // State is available in handlers via axum::Extension<ServerState>
    app.layer(middleware::from_fn(audit_layer))
        .layer(middleware::from_fn(basic_rate_limit))
        .layer(middleware::from_fn(
            crate::middleware_auth::require_auth_stateless,
        ))
        .layer(middleware::from_fn(
            crate::middleware_auth::set_cache_headers,
        ))
        .layer(RequestBodyLimitLayer::new(1_048_576)) // 1 MB
        .layer(TimeoutLayer::new(Duration::from_secs(30)))
        .layer(crate::middleware_auth::cors_layer())
        .layer(CompressionLayer::new().gzip(true))
        .layer(middleware::from_fn(telemetry_layer))
        .layer(axum::Extension(state))
}

async fn health_handler() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "timestamp": chrono::Utc::now().to_rfc3339(),
    }))
}

async fn telemetry_handler() -> Json<serde_json::Value> {
    Json(crate::middleware_telemetry::snapshot())
}

async fn deep_health_handler(
    axum::Extension(state): axum::Extension<ServerState>,
) -> Json<serde_json::Value> {
    let components = state.health.check_all();
    Json(serde_json::json!({
        "components": components.iter().map(|c| {
            serde_json::json!({
                "name": c.name,
                "status": format!("{:?}", c.status),
            })
        }).collect::<Vec<_>>(),
    }))
}

async fn metrics_handler(
    axum::Extension(state): axum::Extension<ServerState>,
) -> Json<serde_json::Value> {
    let collected = state.metrics.collect_all();
    Json(serde_json::json!({ "metrics": collected }))
}

/// Rate limit middleware.
async fn basic_rate_limit(req: Request<Body>, next: Next) -> Response {
    static LIMITER: std::sync::OnceLock<RateLimiter> = std::sync::OnceLock::new();
    let limiter = LIMITER.get_or_init(RateLimiter::default);

    let path = req.uri().path().to_string();
    if path.starts_with("/ws/") || path.contains("/stream") {
        return next.run(req).await;
    }
    let category = endpoint_category(&path);
    let (limit, window) = match *req.method() {
        Method::GET => (600, Duration::from_secs(60)),
        _ => (300, Duration::from_secs(60)),
    };
    let client_ip = "unknown".to_string();
    if !limiter.allow(category, client_ip, limit, window).await {
        return (
            StatusCode::TOO_MANY_REQUESTS,
            Json(serde_json::json!({ "error": "Rate limit exceeded" })),
        )
            .into_response();
    }
    next.run(req).await
}

/// Audit wrapper: extracts state from Extension layer.
async fn audit_layer(req: Request<Body>, next: Next) -> Response {
    let state = req.extensions().get::<ServerState>().cloned();
    let method = req.method().clone();
    let resource = req.uri().path().to_string();

    let resp = next.run(req).await;

    if let Some(state) = state {
        if matches!(method, Method::POST | Method::PUT | Method::DELETE)
            && resp.status().is_success()
        {
            let action = method.as_str().to_string();
            let detail = resp.status().as_u16().to_string();
            if let Ok(conn) = state.get_conn() {
                let _ = conn.execute(
                    "INSERT INTO audit_log (agent, action, resource, detail) \
                     VALUES ('system', ?1, ?2, ?3)",
                    rusqlite::params![action, resource, detail],
                );
            }
        }
    }
    resp
}

#[cfg(test)]
mod tests {
    #[test]
    fn router_builds_without_extensions() {
        use super::*;
        use convergio_db::pool::create_memory_pool;
        use convergio_telemetry::health::HealthRegistry;
        use convergio_telemetry::metrics::MetricsCollector;
        use convergio_types::config::ConvergioConfig;
        use std::sync::RwLock;

        let pool = create_memory_pool().unwrap();
        let state = ServerState::new(
            pool,
            Arc::new(RwLock::new(ConvergioConfig::default())),
            Arc::new(HealthRegistry::new()),
            Arc::new(MetricsCollector::new()),
            true,
        );
        let ctx = AppContext::new();
        let _router = build_router(state, &[], &ctx);
    }
}
