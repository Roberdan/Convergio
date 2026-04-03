//! BackupExtension — impl Extension for the backup module.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// The Extension entry point for data retention, backup & disaster recovery.
pub struct BackupExtension {
    pool: ConnPool,
}

impl BackupExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }
}

impl Default for BackupExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for BackupExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-backup".to_string(),
            description: "Data retention, backup, disaster recovery, \
                          and org data export/import"
                .to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Core,
            provides: vec![
                Capability {
                    name: "data-retention".to_string(),
                    version: "1.0".to_string(),
                    description: "Auto-purge expired data with configurable policies".to_string(),
                },
                Capability {
                    name: "db-backup".to_string(),
                    version: "1.0".to_string(),
                    description: "Periodic SQLite snapshots with WAL checkpoint".to_string(),
                },
                Capability {
                    name: "disaster-recovery".to_string(),
                    version: "1.0".to_string(),
                    description: "Restore daemon to a known state from snapshot".to_string(),
                },
                Capability {
                    name: "org-export-import".to_string(),
                    version: "1.0".to_string(),
                    description: "Export/import org data for cross-node migration".to_string(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("backup: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM backup_snapshots", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "backup_snapshots table inaccessible".into(),
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
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM backup_snapshots", [], |r| {
            r.get::<_, f64>(0)
        }) {
            metrics.push(Metric {
                name: "backup.snapshots.total".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COALESCE(SUM(rows_deleted), 0) FROM backup_purge_log",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "backup.purge.total_rows_deleted".into(),
                value: n,
                labels: vec![],
            });
        }
        metrics
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![
            ScheduledTask {
                name: "auto-purge",
                cron: "0 3 * * *", // daily at 3 AM
            },
            ScheduledTask {
                name: "auto-snapshot",
                cron: "0 4 * * *", // daily at 4 AM
            },
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_correct_id() {
        let ext = BackupExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-backup");
        assert_eq!(m.provides.len(), 4);
    }

    #[test]
    fn migrations_are_returned() {
        let ext = BackupExtension::default();
        let migs = ext.migrations();
        assert_eq!(migs.len(), 2);
    }

    #[test]
    fn health_ok_with_memory_pool() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = BackupExtension::new(pool);
        assert!(matches!(ext.health(), Health::Ok));
    }

    #[test]
    fn scheduled_tasks_declared() {
        let ext = BackupExtension::default();
        let tasks = ext.scheduled_tasks();
        assert_eq!(tasks.len(), 2);
        assert_eq!(tasks[0].name, "auto-purge");
        assert_eq!(tasks[1].name, "auto-snapshot");
    }

    #[test]
    fn metrics_with_empty_db() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = BackupExtension::new(pool);
        let m = ext.metrics();
        assert_eq!(m.len(), 2);
        assert_eq!(m[0].value, 0.0);
    }
}
