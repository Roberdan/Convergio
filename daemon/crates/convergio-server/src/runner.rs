//! HTTP server runner with graceful shutdown.

use crate::state::ApiError;
use axum::Router;

/// Run the Axum server on the given bind address with graceful shutdown.
pub async fn run_server(bind_addr: &str, router: Router) -> Result<(), ApiError> {
    let listener = tokio::net::TcpListener::bind(bind_addr)
        .await
        .map_err(|e| ApiError::internal(format!("bind failed on {bind_addr}: {e}")))?;
    tracing::info!("[server] Listening on {bind_addr}");
    axum::serve(listener, router.into_make_service())
        .with_graceful_shutdown(shutdown_signal())
        .await
        .map_err(|e| ApiError::internal(format!("server runtime failed: {e}")))
}

async fn shutdown_signal() {
    let ctrl_c = async {
        if let Err(e) = tokio::signal::ctrl_c().await {
            tracing::warn!("ctrl_c signal handler failed: {e}");
        }
    };
    #[cfg(unix)]
    let terminate = async {
        use tokio::signal::unix::{signal, SignalKind};
        if let Ok(mut sigterm) = signal(SignalKind::terminate()) {
            sigterm.recv().await;
        }
    };
    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {}
        _ = terminate => {}
    }
    tracing::info!("[server] Shutdown signal received");
}

/// Determine the effective bind address (dev-mode safety check).
pub fn resolve_bind_addr(requested: &str, dev_mode: bool) -> String {
    let has_token = std::env::var("CONVERGIO_AUTH_TOKEN")
        .map(|v| !v.is_empty())
        .unwrap_or(false);
    resolve_bind_addr_inner(requested, dev_mode, has_token)
}

fn resolve_bind_addr_inner(requested: &str, dev_mode: bool, has_token: bool) -> String {
    if dev_mode && !has_token && !requested.starts_with("127.0.0.1") {
        tracing::warn!(
            "dev-mode without CONVERGIO_AUTH_TOKEN: binding to {requested} \
             exposes an unauthenticated server"
        );
    }
    requested.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dev_mode_no_token_respects_requested() {
        let addr = resolve_bind_addr_inner("0.0.0.0:8420", true, false);
        assert_eq!(addr, "0.0.0.0:8420");
    }

    #[test]
    fn dev_mode_with_token_keeps_addr() {
        let addr = resolve_bind_addr_inner("0.0.0.0:8420", true, true);
        assert_eq!(addr, "0.0.0.0:8420");
    }

    #[test]
    fn production_mode_keeps_addr() {
        let addr = resolve_bind_addr_inner("0.0.0.0:8420", false, false);
        assert_eq!(addr, "0.0.0.0:8420");
    }

    #[test]
    fn localhost_in_dev_mode_safe() {
        let addr = resolve_bind_addr_inner("127.0.0.1:8420", true, false);
        assert_eq!(addr, "127.0.0.1:8420");
    }
}
