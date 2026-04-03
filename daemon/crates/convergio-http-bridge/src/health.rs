//! Health check polling for HTTP extensions.
//!
//! Periodically GETs each extension's health endpoint.
//! Transitions: registered/active → active (on success), → degraded (on failure).
//! After MAX_FAILURES consecutive failures → removed.

use crate::store;
use crate::types::{BridgeState, HttpExtension, HEALTH_CHECK_INTERVAL_SECS, MAX_FAILURES};
use convergio_db::pool::ConnPool;
use std::time::Duration;
use tracing::{info, warn};

/// Check a single extension's health by GETting its health endpoint.
/// Returns true if healthy.
pub async fn check_one(client: &reqwest::Client, ext: &HttpExtension) -> bool {
    let url = format!("{}{}", ext.base_url, ext.health_endpoint);
    match client
        .get(&url)
        .timeout(Duration::from_secs(5))
        .send()
        .await
    {
        Ok(resp) if resp.status().is_success() => true,
        Ok(resp) => {
            warn!(
                ext_id = %ext.id, status = %resp.status(),
                "health check returned non-success"
            );
            false
        }
        Err(e) => {
            warn!(ext_id = %ext.id, error = %e, "health check failed");
            false
        }
    }
}

/// Run one health check cycle for all active/registered extensions.
pub async fn check_all(pool: &ConnPool, client: &reqwest::Client) {
    let extensions = {
        let conn = match pool.get() {
            Ok(c) => c,
            Err(e) => {
                warn!(error = %e, "cannot get DB conn for health check");
                return;
            }
        };
        match store::list_active(&conn) {
            Ok(list) => list,
            Err(e) => {
                warn!(error = %e, "cannot list extensions for health check");
                return;
            }
        }
    };

    for ext in &extensions {
        if ext.state == BridgeState::Removed {
            continue;
        }
        let healthy = check_one(client, ext).await;
        let (new_state, failures) = if healthy {
            (BridgeState::Active, 0)
        } else {
            let f = ext.consecutive_failures + 1;
            if f >= MAX_FAILURES {
                info!(ext_id = %ext.id, "removing after {f} consecutive failures");
                (BridgeState::Removed, f)
            } else {
                (BridgeState::Degraded, f)
            }
        };
        if let Ok(conn) = pool.get() {
            let _ = store::update_health(&conn, &ext.id, new_state, failures);
        }
    }
}

/// Spawn the background health check polling loop.
pub fn spawn_poller(pool: ConnPool, shutdown: tokio::sync::watch::Receiver<bool>) {
    let client = reqwest::Client::new();
    tokio::spawn(async move {
        let interval = Duration::from_secs(HEALTH_CHECK_INTERVAL_SECS);
        loop {
            tokio::time::sleep(interval).await;
            if *shutdown.borrow() {
                info!("health check poller shutting down");
                break;
            }
            check_all(&pool, &client).await;
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn max_failures_constant() {
        assert!(MAX_FAILURES >= 3, "need at least 3 retries before removal");
    }
}
