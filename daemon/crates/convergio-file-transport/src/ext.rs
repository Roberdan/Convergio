//! FileTransportExtension — impl Extension for file transport.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

/// Extension entry point for rsync-based file transport.
pub struct FileTransportExtension {
    pool: ConnPool,
}

impl FileTransportExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }
}

impl Default for FileTransportExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for FileTransportExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-file-transport".to_string(),
            description: "Rsync-based file transport between mesh nodes".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![Capability {
                name: "file-transport".to_string(),
                version: "1.0.0".to_string(),
                description: "Push/pull files between mesh peers via rsync".to_string(),
            }],
            requires: vec![Dependency {
                capability: "db-pool".to_string(),
                version_req: ">=1.0.0".to_string(),
                required: true,
            }],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::file_transport_routes(self.pool.clone()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("file-transport: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM file_transfers", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "file_transfers table inaccessible".into(),
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
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM file_transfers", [], |r| {
            r.get::<_, f64>(0)
        }) {
            metrics.push(Metric {
                name: "file_transport.transfers.total".into(),
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
        let ext = FileTransportExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-file-transport");
        assert_eq!(m.provides.len(), 1);
        assert_eq!(m.provides[0].name, "file-transport");
    }

    #[test]
    fn migrations_are_returned() {
        let ext = FileTransportExtension::default();
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
        let ext = FileTransportExtension::new(pool);
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
        let ext = FileTransportExtension::new(pool);
        let m = ext.metrics();
        assert_eq!(m.len(), 1);
        assert_eq!(m[0].value, 0.0);
    }
}
