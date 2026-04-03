//! MultitenancyExtension — Extension trait implementation.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

use crate::routes::TenancyState;

/// Multi-tenancy extension — DB isolation, network whitelist, secret scoping,
/// audit isolation, resource limits.
pub struct MultitenancyExtension {
    pool: ConnPool,
}

impl MultitenancyExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn state(&self) -> Arc<TenancyState> {
        Arc::new(TenancyState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for MultitenancyExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-multitenancy".to_string(),
            description: "Multi-tenancy: org isolation, secrets, audit, resource limits".into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "db-isolation".into(),
                    version: "1.0".into(),
                    description: "Per-org table prefix enforcement".into(),
                },
                Capability {
                    name: "network-isolation".into(),
                    version: "1.0".into(),
                    description: "Per-org peer whitelist for mesh sync".into(),
                },
                Capability {
                    name: "secret-isolation".into(),
                    version: "1.0".into(),
                    description: "Per-org keychain scoping".into(),
                },
                Capability {
                    name: "audit-isolation".into(),
                    version: "1.0".into(),
                    description: "Per-org audit trail with hash chain".into(),
                },
                Capability {
                    name: "resource-limits".into(),
                    version: "1.0".into(),
                    description: "Per-org soft resource tracking".into(),
                },
            ],
            requires: vec![Dependency {
                capability: "db-pool".into(),
                version_req: ">=1.0.0".into(),
                required: true,
            }],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::tenancy_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("multitenancy: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM mt_isolation_policies", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "mt_isolation_policies inaccessible".into(),
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
        let mut out = Vec::new();

        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM mt_isolation_policies", [], |r| {
            r.get::<_, f64>(0)
        }) {
            out.push(Metric {
                name: "multitenancy.orgs_configured".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM mt_isolation_violations", [], |r| {
            r.get::<_, f64>(0)
        }) {
            out.push(Metric {
                name: "multitenancy.violations_total".into(),
                value: n,
                labels: vec![],
            });
        }

        out
    }
}
