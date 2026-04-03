//! Extension trait implementation for convergio-agents.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// The agents catalog extension.
pub struct AgentsCatalogExtension {
    pool: ConnPool,
}

impl AgentsCatalogExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }
}

impl Extension for AgentsCatalogExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-agents".into(),
            description: "Agent catalog — definitions, categories, spawn specs".into(),
            version: env!("CARGO_PKG_VERSION").into(),
            kind: ModuleKind::Platform,
            provides: vec![Capability {
                name: "agent-catalog".into(),
                version: "1.0".into(),
                description: "CRUD for agent specifications with category taxonomy".into(),
            }],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::catalog_routes(self.pool.clone()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        let conn = self.pool.get().map_err(|e| e.to_string())?;
        match crate::seed::run(&conn) {
            Ok(n) => tracing::info!(inserted = n, "agent catalog seeded"),
            Err(e) => tracing::warn!("agent catalog seed failed: {e}"),
        }
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => match crate::store::count_active(&conn) {
                Ok(_) => Health::Ok,
                Err(e) => Health::Degraded {
                    reason: format!("agent catalog: {e}"),
                },
            },
            Err(e) => Health::Down {
                reason: format!("pool: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let conn = match self.pool.get() {
            Ok(c) => c,
            Err(_) => return vec![],
        };
        let mut out = vec![];
        if let Ok(n) = crate::store::count_active(&conn) {
            out.push(Metric {
                name: "agents.catalog.active".into(),
                value: n as f64,
                labels: vec![],
            });
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_ext() -> AgentsCatalogExtension {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "agents", &crate::schema::migrations())
            .unwrap();
        drop(conn);
        AgentsCatalogExtension::new(pool)
    }

    #[test]
    fn manifest_correct() {
        let ext = make_ext();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-agents");
        assert_eq!(m.provides.len(), 1);
    }

    #[test]
    fn health_ok() {
        let ext = make_ext();
        assert!(matches!(ext.health(), Health::Ok));
    }
}
