//! Extension trait implementation for convergio-http-bridge.

use crate::{handlers, health, proxy, schema, store};
use convergio_db::pool::ConnPool;
use convergio_telemetry::health::{ComponentHealth, HealthCheck};
use convergio_telemetry::metrics::MetricSource;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};
use std::sync::Mutex;

/// The HTTP Extension bridge — manages external extension lifecycle.
pub struct HttpBridgeExtension {
    pool: Option<ConnPool>,
    shutdown_tx: Mutex<Option<tokio::sync::watch::Sender<bool>>>,
}

impl Default for HttpBridgeExtension {
    fn default() -> Self {
        Self::new()
    }
}

impl HttpBridgeExtension {
    pub fn new() -> Self {
        Self {
            pool: None,
            shutdown_tx: Mutex::new(None),
        }
    }

    pub fn with_pool(pool: ConnPool) -> Self {
        Self {
            pool: Some(pool),
            shutdown_tx: Mutex::new(None),
        }
    }
}

impl Extension for HttpBridgeExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-http-bridge".to_string(),
            description: "HTTP extension bridge — register external extensions \
                          in any language via REST API"
                .to_string(),
            version: "0.1.0".to_string(),
            kind: ModuleKind::Core,
            provides: vec![Capability {
                name: "http-bridge".to_string(),
                version: "0.1.0".to_string(),
                description: "Register, health-check, and proxy HTTP extensions".to_string(),
            }],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        schema::migrations()
    }

    fn routes(&self, ctx: &AppContext) -> Option<axum::Router> {
        let _ = ctx;
        let router = axum::Router::new()
            .route(
                "/api/extensions/register",
                axum::routing::post(handlers::register_extension),
            )
            .route(
                "/api/extensions",
                axum::routing::get(handlers::list_extensions),
            )
            .route(
                "/api/extensions/{id}",
                axum::routing::get(handlers::get_extension).delete(handlers::remove_extension),
            )
            .merge(proxy::proxy_routes());
        Some(router)
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        if let Some(pool) = &self.pool {
            let (tx, rx) = tokio::sync::watch::channel(false);
            health::spawn_poller(pool.clone(), rx);
            if let Ok(mut guard) = self.shutdown_tx.lock() {
                *guard = Some(tx);
            }
            tracing::info!("HTTP bridge health poller started");
        }
        Ok(())
    }

    fn on_shutdown(&self) -> ExtResult<()> {
        if let Ok(mut guard) = self.shutdown_tx.lock() {
            if let Some(tx) = guard.take() {
                let _ = tx.send(true);
            }
        }
        Ok(())
    }

    fn health(&self) -> Health {
        match &self.pool {
            Some(pool) => match pool.get() {
                Ok(conn) => match store::list_active(&conn) {
                    Ok(_) => Health::Ok,
                    Err(e) => Health::Degraded {
                        reason: format!("cannot query extensions: {e}"),
                    },
                },
                Err(e) => Health::Degraded {
                    reason: format!("db pool: {e}"),
                },
            },
            None => Health::Degraded {
                reason: "no pool configured".to_string(),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let pool = match &self.pool {
            Some(p) => p,
            None => return vec![],
        };
        let conn = match pool.get() {
            Ok(c) => c,
            Err(_) => return vec![],
        };
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM http_extensions WHERE state != 'removed'",
                [],
                |r| r.get(0),
            )
            .unwrap_or(0);
        vec![Metric {
            name: "http_bridge.active_extensions".to_string(),
            value: count as f64,
            labels: vec![],
        }]
    }
}

impl HealthCheck for HttpBridgeExtension {
    fn name(&self) -> &str {
        "http-bridge"
    }

    fn check(&self) -> ComponentHealth {
        ComponentHealth {
            name: "http-bridge".to_string(),
            status: self.health(),
            message: None,
        }
    }
}

impl MetricSource for HttpBridgeExtension {
    fn name(&self) -> &str {
        "http-bridge"
    }

    fn collect(&self) -> Vec<Metric> {
        self.metrics()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_is_valid() {
        let ext = HttpBridgeExtension::new();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-http-bridge");
        assert!(matches!(m.kind, ModuleKind::Core));
        assert_eq!(m.provides.len(), 1);
        assert_eq!(m.provides[0].name, "http-bridge");
    }

    #[test]
    fn migrations_returned() {
        let ext = HttpBridgeExtension::new();
        assert_eq!(ext.migrations().len(), 2);
    }

    #[test]
    fn health_without_pool_is_degraded() {
        let ext = HttpBridgeExtension::new();
        assert!(matches!(ext.health(), Health::Degraded { .. }));
    }

    #[test]
    fn health_with_pool_ok() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = HttpBridgeExtension::with_pool(pool);
        assert!(matches!(ext.health(), Health::Ok));
    }

    #[test]
    fn metrics_count_extensions() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = HttpBridgeExtension::with_pool(pool);
        let metrics = ext.metrics();
        assert_eq!(metrics.len(), 1);
        assert_eq!(metrics[0].value, 0.0);
    }
}
