//! DelegationExtension — impl Extension for delegation orchestrator.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

/// Extension entry point for the delegation orchestrator.
pub struct DelegationExtension {
    pool: ConnPool,
}

impl DelegationExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }
}

impl Default for DelegationExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for DelegationExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-delegation".to_string(),
            description: "Delegation orchestrator — copy, spawn, monitor, sync, notify".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "delegation-pipeline".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Full delegation pipeline: copy, spawn, monitor, sync".to_string(),
                },
                Capability {
                    name: "remote-spawn".to_string(),
                    version: "1.0.0".to_string(),
                    description: "SSH-based remote agent spawning on mesh peers".to_string(),
                },
            ],
            requires: vec![
                Dependency {
                    capability: "db-pool".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
                Dependency {
                    capability: "file-transport".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
                Dependency {
                    capability: "peer-sync".to_string(),
                    version_req: ">=0.1.0".to_string(),
                    required: false,
                },
            ],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::delegation_routes(self.pool.clone()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("delegation: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM delegations", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "delegations table inaccessible".into(),
                    }
                }
            }
            Err(e) => Health::Down {
                reason: format!("pool error: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let conn = match self.pool.get() {
            Ok(c) => c,
            Err(_) => return vec![],
        };
        let mut metrics = Vec::new();
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM delegations", [], |r| {
            r.get::<_, f64>(0)
        }) {
            metrics.push(Metric {
                name: "delegation.total".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM delegations \
             WHERE status NOT IN ('done', 'pending') AND status NOT LIKE 'failed%'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "delegation.active".into(),
                value: n,
                labels: vec![],
            });
        }
        metrics
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ext_with_schema() -> DelegationExtension {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        DelegationExtension::new(pool)
    }

    #[test]
    fn manifest_has_correct_id() {
        let ext = DelegationExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-delegation");
        assert_eq!(m.provides.len(), 2);
        assert_eq!(m.provides[0].name, "delegation-pipeline");
        assert_eq!(m.provides[1].name, "remote-spawn");
    }

    #[test]
    fn migrations_are_returned() {
        let ext = DelegationExtension::default();
        assert_eq!(ext.migrations().len(), 1);
    }

    #[test]
    fn health_ok_with_schema() {
        let ext = ext_with_schema();
        assert!(matches!(ext.health(), Health::Ok));
    }

    #[test]
    fn metrics_with_empty_db() {
        let ext = ext_with_schema();
        let m = ext.metrics();
        assert_eq!(m.len(), 2);
        assert_eq!(m[0].name, "delegation.total");
        assert_eq!(m[0].value, 0.0);
        assert_eq!(m[1].name, "delegation.active");
        assert_eq!(m[1].value, 0.0);
    }
}
