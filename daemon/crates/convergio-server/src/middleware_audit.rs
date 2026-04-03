//! Audit middleware: records POST/PUT/DELETE mutations to audit_log.
//! Runs after response — never blocks the request path.

use axum::body::Body;
use axum::extract::ConnectInfo;
use axum::http::{Method, Request};
use axum::middleware::Next;
use axum::response::Response;
use std::net::SocketAddr;

fn extract_agent(req: &Request<Body>) -> String {
    let header = req
        .headers()
        .get("authorization")
        .and_then(|v| v.to_str().ok());
    let Some(value) = header else {
        return "dev-mode".to_string();
    };
    let Some(token) = value.strip_prefix("Bearer ") else {
        return "legacy".to_string();
    };
    if token.matches('.').count() == 2 {
        match convergio_security::jwt::validate_token(token) {
            Ok(claims) => claims.sub,
            Err(_) => "unknown".to_string(),
        }
    } else {
        "legacy".to_string()
    }
}

fn extract_ip(req: &Request<Body>) -> Option<String> {
    if let Some(addr) = req.extensions().get::<ConnectInfo<SocketAddr>>() {
        return Some(addr.0.ip().to_string());
    }
    req.headers()
        .get("x-forwarded-for")
        .and_then(|v| v.to_str().ok())
        .map(|v| v.split(',').next().unwrap_or(v).trim().to_string())
}

fn is_mutation(method: &Method) -> bool {
    matches!(*method, Method::POST | Method::PUT | Method::DELETE)
}

/// Axum middleware that appends a row to `audit_log` for successful
/// POST, PUT, and DELETE requests.
pub async fn audit_mutations(
    axum::extract::State(state): axum::extract::State<super::state::ServerState>,
    req: Request<Body>,
    next: Next,
) -> Response {
    let method = req.method().clone();
    let resource = req.uri().path().to_string();
    let agent = extract_agent(&req);
    let ip = extract_ip(&req);

    let resp = next.run(req).await;

    if is_mutation(&method) && resp.status().is_success() {
        let action = method.as_str().to_string();
        let detail = resp.status().as_u16().to_string();
        match state.get_conn() {
            Ok(conn) => {
                if let Err(e) = conn.execute(
                    "INSERT INTO audit_log (agent, action, resource, detail, ip_addr) \
                     VALUES (?1, ?2, ?3, ?4, ?5)",
                    rusqlite::params![agent, action, resource, detail, ip],
                ) {
                    tracing::warn!(agent=%agent, resource=%resource, "audit insert failed: {e}");
                }
            }
            Err(e) => {
                tracing::warn!(agent=%agent, resource=%resource, "audit pool exhausted: {e}");
            }
        }
    }
    resp
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::http::Request;

    #[test]
    fn mutation_methods() {
        assert!(is_mutation(&Method::POST));
        assert!(is_mutation(&Method::PUT));
        assert!(is_mutation(&Method::DELETE));
        assert!(!is_mutation(&Method::GET));
    }

    #[test]
    fn extract_agent_no_header() {
        let req = Request::builder().uri("/api/test").body(Body::empty()).unwrap();
        assert_eq!(extract_agent(&req), "dev-mode");
    }

    #[test]
    fn extract_agent_legacy_bearer() {
        let req = Request::builder()
            .uri("/api/test")
            .header("authorization", "Bearer no-dots")
            .body(Body::empty())
            .unwrap();
        assert_eq!(extract_agent(&req), "legacy");
    }

    #[test]
    fn extract_ip_forwarded() {
        let req = Request::builder()
            .uri("/api/test")
            .header("x-forwarded-for", "203.0.113.1, 10.0.0.1")
            .body(Body::empty())
            .unwrap();
        assert_eq!(extract_ip(&req), Some("203.0.113.1".to_string()));
    }

    #[test]
    fn extract_ip_none() {
        let req = Request::builder().uri("/api/test").body(Body::empty()).unwrap();
        assert_eq!(extract_ip(&req), None);
    }

    #[test]
    fn audit_log_insert_logic() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        conn.execute_batch(
            "CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY, agent TEXT, action TEXT NOT NULL,
                resource TEXT, detail TEXT, ip_addr TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
             );"
        ).unwrap();
        conn.execute(
            "INSERT INTO audit_log (agent, action, resource, detail, ip_addr)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            rusqlite::params!["dev-mode", "POST", "/api/plans", "201", Option::<&str>::None],
        ).unwrap();
        let count: i64 = conn.query_row("SELECT COUNT(*) FROM audit_log", [], |r| r.get(0)).unwrap();
        assert_eq!(count, 1);
    }
}
