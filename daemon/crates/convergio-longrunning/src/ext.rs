//! LongRunningExtension — impl Extension for the long-running protocol.

use std::time::Duration;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// The Extension entry point for the long-running execution protocol.
pub struct LongRunningExtension {
    pool: ConnPool,
}

impl LongRunningExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }
}

impl Default for LongRunningExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for LongRunningExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-longrunning".to_string(),
            description: "Long-running execution protocol: heartbeat, \
                          checkpoint, resume, budget guard, delegation chain"
                .to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "heartbeat-monitor".to_string(),
                    version: "1.0".to_string(),
                    description: "Liveness tracking for long-running executions".to_string(),
                },
                Capability {
                    name: "checkpoint-resume".to_string(),
                    version: "1.0".to_string(),
                    description: "Persist and restore execution state".to_string(),
                },
                Capability {
                    name: "budget-guard".to_string(),
                    version: "1.0".to_string(),
                    description: "Stop execution when budget exhausted".to_string(),
                },
                Capability {
                    name: "delegation-chain".to_string(),
                    version: "1.0".to_string(),
                    description: "Tree of delegated executions with cascade".to_string(),
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
        tracing::info!("longrunning: starting heartbeat reaper");
        let reaper_interval = Duration::from_secs(60);
        crate::reaper::spawn_reaper(self.pool.clone(), reaper_interval);
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM lr_executions", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "lr_executions table inaccessible".into(),
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
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM lr_executions WHERE stage = 'running'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "longrunning.executions.active".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM lr_executions WHERE stage = 'reaped'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "longrunning.executions.reaped".into(),
                value: n,
                labels: vec![],
            });
        }
        metrics
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![ScheduledTask {
            name: "heartbeat-reaper",
            cron: "* * * * *",
        }]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_correct_id() {
        let ext = LongRunningExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-longrunning");
        assert_eq!(m.provides.len(), 4);
    }

    #[test]
    fn migrations_are_returned() {
        let ext = LongRunningExtension::default();
        let migs = ext.migrations();
        assert_eq!(migs.len(), 3);
    }

    #[test]
    fn health_ok_with_memory_pool() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = LongRunningExtension::new(pool);
        assert!(matches!(ext.health(), Health::Ok));
    }
}
