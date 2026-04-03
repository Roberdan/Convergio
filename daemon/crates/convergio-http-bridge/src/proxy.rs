//! Route proxy — forwards requests under /api/ext/ to HTTP extensions.
//!
//! When an extension declares routes_prefix="/api/ext/openclaw", any request to
//! /api/ext/openclaw/* is proxied to the extension's base_url.

use axum::body::Body;
use axum::extract::Path;
use axum::http::{Method, Request, StatusCode};
use axum::response::IntoResponse;
use axum::Json;
use convergio_db::pool::ConnPool;
use std::time::Duration;
use tracing::warn;

/// Proxy handler: captures /api/ext/*rest, splits into ext_id + remaining path.
pub async fn proxy_handler(
    axum::Extension(pool): axum::Extension<ConnPool>,
    method: Method,
    Path(rest): Path<String>,
    req: Request<Body>,
) -> impl IntoResponse {
    // rest = "openclaw/some/path" — first segment is ext_id
    let (ext_id, path) = match rest.find('/') {
        Some(idx) => (&rest[..idx], &rest[idx + 1..]),
        None => (rest.as_str(), ""),
    };

    let (base_url, state) = {
        let conn = match pool.get() {
            Ok(c) => c,
            Err(e) => return err_response(StatusCode::INTERNAL_SERVER_ERROR, &format!("db: {e}")),
        };
        match crate::store::get_by_id(&conn, ext_id) {
            Ok(Some(ext)) => (ext.base_url, ext.state),
            Ok(None) => return err_response(StatusCode::NOT_FOUND, "extension not found"),
            Err(e) => return err_response(StatusCode::INTERNAL_SERVER_ERROR, &e),
        }
    };

    if state != crate::types::BridgeState::Active {
        return err_response(StatusCode::SERVICE_UNAVAILABLE, "extension not active");
    }

    let target_url = if path.is_empty() {
        base_url.clone()
    } else {
        format!("{base_url}/{path}")
    };
    forward_request(&target_url, method, req, ext_id).await
}

async fn forward_request(
    url: &str,
    method: Method,
    req: Request<Body>,
    ext_id: &str,
) -> axum::response::Response {
    let client = reqwest::Client::new();
    let builder = match method {
        Method::GET => client.get(url),
        Method::POST => client.post(url),
        Method::PUT => client.put(url),
        Method::DELETE => client.delete(url),
        Method::PATCH => client.patch(url),
        _ => return err_response(StatusCode::METHOD_NOT_ALLOWED, "method not allowed"),
    };
    let mut builder = builder.timeout(Duration::from_secs(30));
    for (name, value) in req.headers() {
        if let Ok(v) = value.to_str() {
            builder = builder.header(name.as_str(), v);
        }
    }
    match builder.send().await {
        Ok(resp) => {
            let status =
                StatusCode::from_u16(resp.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);
            let body = resp.text().await.unwrap_or_default();
            (status, body).into_response()
        }
        Err(e) => {
            warn!(ext_id = %ext_id, error = %e, "proxy request failed");
            err_response(StatusCode::BAD_GATEWAY, &format!("proxy: {e}"))
        }
    }
}

fn err_response(status: StatusCode, msg: &str) -> axum::response::Response {
    (status, Json(serde_json::json!({"error": msg}))).into_response()
}

/// Build the proxy route: /api/ext/{*rest} catches all extension traffic.
pub fn proxy_routes() -> axum::Router {
    axum::Router::new().route("/api/ext/*rest", axum::routing::any(proxy_handler))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn proxy_routes_builds() {
        let _router = proxy_routes();
    }

    #[test]
    fn parse_ext_id_from_path() {
        let rest = "openclaw/contracts/list";
        let (ext_id, path) = match rest.find('/') {
            Some(idx) => (&rest[..idx], &rest[idx + 1..]),
            None => (rest, ""),
        };
        assert_eq!(ext_id, "openclaw");
        assert_eq!(path, "contracts/list");
    }

    #[test]
    fn parse_ext_id_no_subpath() {
        let rest = "openclaw";
        let (ext_id, path) = match rest.find('/') {
            Some(idx) => (&rest[..idx], &rest[idx + 1..]),
            None => (rest, ""),
        };
        assert_eq!(ext_id, "openclaw");
        assert_eq!(path, "");
    }
}
