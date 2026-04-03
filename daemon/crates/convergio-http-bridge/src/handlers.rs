//! Axum handlers for the HTTP extension bridge API.
//!
//! - POST /api/extensions/register — register an external extension
//! - GET  /api/extensions — list all active extensions
//! - GET  /api/extensions/:id — get a single extension
//! - DELETE /api/extensions/:id — remove an extension

use crate::store;
use crate::types::RegisterRequest;
use axum::extract::Path;
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use convergio_db::pool::ConnPool;

/// POST /api/extensions/register
pub async fn register_extension(
    axum::Extension(pool): axum::Extension<ConnPool>,
    Json(req): Json<RegisterRequest>,
) -> impl IntoResponse {
    if let Err(msg) = validate_request(&req) {
        return (StatusCode::BAD_REQUEST, Json(error_body(&msg))).into_response();
    }
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(error_body(&format!("db: {e}"))),
            )
                .into_response()
        }
    };
    // Check for duplicate
    match store::get_by_id(&conn, &req.id) {
        Ok(Some(existing)) if existing.state != crate::types::BridgeState::Removed => {
            return (
                StatusCode::CONFLICT,
                Json(error_body(&format!(
                    "extension '{}' already registered",
                    req.id
                ))),
            )
                .into_response()
        }
        _ => {}
    }
    match store::insert_extension(&conn, &req) {
        Ok(()) => {
            tracing::info!(ext_id = %req.id, "HTTP extension registered");
            (
                StatusCode::CREATED,
                Json(serde_json::json!({"id": req.id, "status": "registered"})),
            )
                .into_response()
        }
        Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(error_body(&e))).into_response(),
    }
}

/// GET /api/extensions
pub async fn list_extensions(
    axum::Extension(pool): axum::Extension<ConnPool>,
) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(error_body(&format!("db: {e}"))),
            )
                .into_response()
        }
    };
    match store::list_active(&conn) {
        Ok(list) => Json(serde_json::json!({"extensions": list})).into_response(),
        Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(error_body(&e))).into_response(),
    }
}

/// GET /api/extensions/:id
pub async fn get_extension(
    axum::Extension(pool): axum::Extension<ConnPool>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(error_body(&format!("db: {e}"))),
            )
                .into_response()
        }
    };
    match store::get_by_id(&conn, &id) {
        Ok(Some(ext)) => Json(serde_json::json!(ext)).into_response(),
        Ok(None) => (
            StatusCode::NOT_FOUND,
            Json(error_body(&format!("extension '{id}' not found"))),
        )
            .into_response(),
        Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(error_body(&e))).into_response(),
    }
}

/// DELETE /api/extensions/:id
pub async fn remove_extension(
    axum::Extension(pool): axum::Extension<ConnPool>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(error_body(&format!("db: {e}"))),
            )
                .into_response()
        }
    };
    match store::remove_extension(&conn, &id) {
        Ok(true) => {
            tracing::info!(ext_id = %id, "HTTP extension removed");
            StatusCode::NO_CONTENT.into_response()
        }
        Ok(false) => (
            StatusCode::NOT_FOUND,
            Json(error_body(&format!("extension '{id}' not found"))),
        )
            .into_response(),
        Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(error_body(&e))).into_response(),
    }
}

fn validate_request(req: &RegisterRequest) -> Result<(), String> {
    if req.id.is_empty() {
        return Err("id is required".into());
    }
    if req.base_url.is_empty() {
        return Err("base_url is required".into());
    }
    if !req.routes_prefix.starts_with("/api/ext/") {
        return Err("routes_prefix must start with /api/ext/".into());
    }
    Ok(())
}

fn error_body(msg: &str) -> serde_json::Value {
    serde_json::json!({
        "error": {
            "code": 400,
            "message": msg,
            "timestamp": chrono::Utc::now().to_rfc3339(),
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_rejects_empty_id() {
        let req = RegisterRequest {
            id: String::new(),
            manifest: convergio_types::manifest::Manifest {
                id: String::new(),
                description: String::new(),
                version: "1.0.0".to_string(),
                kind: convergio_types::manifest::ModuleKind::Integration,
                provides: vec![],
                requires: vec![],
                agent_tools: vec![],
            },
            base_url: "http://localhost:3100".into(),
            health_endpoint: "/health".into(),
            events_webhook: "/webhook/events".into(),
            routes_prefix: "/api/ext/test".into(),
        };
        assert!(validate_request(&req).is_err());
    }

    #[test]
    fn validate_rejects_bad_prefix() {
        let req = RegisterRequest {
            id: "test".into(),
            manifest: convergio_types::manifest::Manifest {
                id: "test".to_string(),
                description: String::new(),
                version: "1.0.0".to_string(),
                kind: convergio_types::manifest::ModuleKind::Integration,
                provides: vec![],
                requires: vec![],
                agent_tools: vec![],
            },
            base_url: "http://localhost:3100".into(),
            health_endpoint: "/health".into(),
            events_webhook: "/webhook/events".into(),
            routes_prefix: "/wrong/prefix".into(),
        };
        assert!(validate_request(&req).is_err());
    }

    #[test]
    fn validate_accepts_valid_request() {
        let req = RegisterRequest {
            id: "openclaw-bridge".into(),
            manifest: convergio_types::manifest::Manifest {
                id: "openclaw-bridge".to_string(),
                description: "Legal AI".to_string(),
                version: "1.0.0".to_string(),
                kind: convergio_types::manifest::ModuleKind::Integration,
                provides: vec![],
                requires: vec![],
                agent_tools: vec![],
            },
            base_url: "http://localhost:3100".into(),
            health_endpoint: "/health".into(),
            events_webhook: "/webhook/events".into(),
            routes_prefix: "/api/ext/openclaw".into(),
        };
        assert!(validate_request(&req).is_ok());
    }
}
