//! Authentication middleware — JWT, legacy Bearer, dev-mode, localhost bypass.

use axum::body::Body;
use axum::extract::ConnectInfo;
use axum::http::{Method, Request, StatusCode};
use axum::middleware::Next;
use axum::response::{IntoResponse, Response};
use axum::Json;
use constant_time_eq::constant_time_eq;
use convergio_security::jwt::{self, AgentClaims};
use convergio_security::rbac;
use std::env;
use std::sync::OnceLock;
use tower_http::cors::CorsLayer;

static AUTH_TOKEN: OnceLock<Option<String>> = OnceLock::new();

fn get_auth_token() -> &'static Option<String> {
    AUTH_TOKEN.get_or_init(|| match env::var("CONVERGIO_AUTH_TOKEN") {
        Ok(t) if !t.is_empty() => Some(t),
        _ => None,
    })
}

fn compare_tokens(a: &str, b: &str) -> bool {
    constant_time_eq(a.as_bytes(), b.as_bytes())
}

/// Routes that never require auth.
const EXEMPT_ROUTES: &[&str] = &["/api/health"];

fn needs_auth(path: &str) -> bool {
    !EXEMPT_ROUTES.contains(&path)
}

fn is_localhost(req: &Request<Body>) -> bool {
    if req.headers().contains_key("x-forwarded-for") {
        return false;
    }
    if let Some(addr) = req.extensions().get::<ConnectInfo<std::net::SocketAddr>>() {
        return addr.0.ip().is_loopback();
    }
    false
}

fn authenticate(header_value: Option<&str>, dev_mode: bool) -> Result<Option<AgentClaims>, ()> {
    if let Some(token) = header_value.and_then(|v| v.strip_prefix("Bearer ")) {
        // JWT tokens have 2 dots; legacy tokens do not
        if token.matches('.').count() == 2 {
            return match jwt::validate_token(token) {
                Ok(claims) => Ok(Some(claims)),
                Err(e) => {
                    tracing::warn!("JWT validation failed: {e}");
                    Err(())
                }
            };
        }
        // Legacy shared bearer token
        if let Some(expected) = get_auth_token() {
            if compare_tokens(token, expected.as_str()) {
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_secs())
                    .unwrap_or(0);
                return Ok(Some(AgentClaims {
                    sub: "system-bearer".to_string(),
                    role: jwt::AgentRole::Coordinator,
                    cap: vec!["*".to_string()],
                    iat: now,
                    exp: u64::MAX,
                }));
            }
        }
        return Err(());
    }
    // No Authorization header
    match get_auth_token() {
        None if dev_mode => Ok(None),
        _ => Err(()),
    }
}

/// Axum middleware: authenticates via JWT, legacy bearer, or dev-mode.
/// /api/health is exempt. Localhost skips auth.
/// Extracts ServerState from tower Extension layer (not Axum State).
pub async fn require_auth_stateless(req: Request<Body>, next: Next) -> Response {
    let path = req.uri().path().to_string();
    if !needs_auth(&path) {
        return next.run(req).await;
    }
    if is_localhost(&req) {
        return next.run(req).await;
    }
    let dev_mode = req
        .extensions()
        .get::<super::state::ServerState>()
        .map(|s| s.dev_mode)
        .unwrap_or(false);
    let auth_header = req
        .headers()
        .get("authorization")
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string());

    match authenticate(auth_header.as_deref(), dev_mode) {
        Ok(Some(claims)) => {
            if !rbac::role_can_access(&claims.role, &path) {
                tracing::warn!(
                    agent = %claims.sub, role = %claims.role,
                    path = %path, "RBAC denied"
                );
                return (
                    StatusCode::FORBIDDEN,
                    Json(serde_json::json!({
                        "error": "Forbidden",
                        "message": format!("Role '{}' cannot access {path}", claims.role)
                    })),
                )
                    .into_response();
            }
            next.run(req).await
        }
        Ok(None) => next.run(req).await,
        Err(()) => (
            StatusCode::UNAUTHORIZED,
            Json(serde_json::json!({
                "error": "Unauthorized",
                "message": "Valid Bearer token required"
            })),
        )
            .into_response(),
    }
}

/// Cache-Control header middleware.
pub async fn set_cache_headers(req: Request<Body>, next: Next) -> Response {
    let mut res = next.run(req).await;
    if !res
        .headers()
        .contains_key(axum::http::header::CACHE_CONTROL)
    {
        res.headers_mut().insert(
            axum::http::header::CACHE_CONTROL,
            axum::http::HeaderValue::from_static("private, max-age=10"),
        );
    }
    res
}

/// Build the CORS layer from env or defaults.
pub fn cors_layer() -> CorsLayer {
    let origins = env::var("CONVERGIO_CORS_ORIGINS")
        .ok()
        .and_then(|value| {
            let parsed: Vec<_> = value
                .split(',')
                .map(str::trim)
                .filter(|o| !o.is_empty())
                .filter_map(|o| axum::http::HeaderValue::from_str(o).ok())
                .collect();
            if parsed.is_empty() {
                None
            } else {
                Some(parsed)
            }
        })
        .unwrap_or_else(|| {
            vec![
                axum::http::HeaderValue::from_static("http://localhost:8420"),
                axum::http::HeaderValue::from_static("http://127.0.0.1:8420"),
                axum::http::HeaderValue::from_static("http://localhost:3000"),
                axum::http::HeaderValue::from_static("tauri://localhost"),
            ]
        });

    CorsLayer::new()
        .allow_origin(origins)
        .allow_methods([
            Method::GET,
            Method::POST,
            Method::PUT,
            Method::DELETE,
            Method::OPTIONS,
        ])
        .allow_headers([
            axum::http::header::CONTENT_TYPE,
            axum::http::header::AUTHORIZATION,
            axum::http::header::ACCEPT,
        ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exempt_routes_skip_auth() {
        assert!(!needs_auth("/api/health"));
    }

    #[test]
    fn normal_routes_need_auth() {
        assert!(needs_auth("/api/plans"));
    }
}
