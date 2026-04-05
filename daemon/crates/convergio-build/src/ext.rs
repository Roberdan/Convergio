//! BuildExtension — impl Extension for the self-build module.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// The Extension entry point for self-build.
pub struct BuildExtension {
    pool: ConnPool,
}

impl BuildExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }
}

impl Default for BuildExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for BuildExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-build".to_string(),
            description: "Self-build: the daemon builds, tests, and deploys itself".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "self-build".to_string(),
                    version: "1.0".to_string(),
                    description: "Build the daemon from source (check, test, release)".to_string(),
                },
                Capability {
                    name: "self-deploy".to_string(),
                    version: "1.0".to_string(),
                    description: "Deploy new binary with launchd restart and rollback".to_string(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        let state = std::sync::Arc::new(crate::routes::BuildState {
            pool: self.pool.clone(),
        });
        Some(crate::routes::router(state))
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("build: self-build extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM build_history", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "build_history table inaccessible".into(),
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
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM build_history", [], |r| {
            r.get::<_, f64>(0)
        }) {
            metrics.push(Metric {
                name: "build.total".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM build_history WHERE status='succeeded'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "build.succeeded".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM build_history WHERE status='deployed'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "build.deployed".into(),
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

    #[test]
    fn manifest_has_correct_id() {
        let ext = BuildExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-build");
        assert_eq!(m.provides.len(), 2);
    }

    #[test]
    fn migrations_are_returned() {
        let ext = BuildExtension::default();
        let migs = ext.migrations();
        assert_eq!(migs.len(), 1);
    }

    #[test]
    fn health_ok_with_memory_pool() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = BuildExtension::new(pool);
        assert!(matches!(ext.health(), Health::Ok));
    }

    #[test]
    fn metrics_with_empty_db() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = BuildExtension::new(pool);
        let m = ext.metrics();
        assert_eq!(m.len(), 3);
        assert_eq!(m[0].value, 0.0);
    }
}
