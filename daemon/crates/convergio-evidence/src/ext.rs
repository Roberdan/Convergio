// EvidenceExtension — impl Extension for evidence gate + workflow automation.

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

pub struct EvidenceExtension {
    pool: ConnPool,
}

impl EvidenceExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }
}

impl Extension for EvidenceExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-evidence".to_string(),
            description: "Evidence gate, checklist enforcement, workflow automation".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "evidence-gate".to_string(),
                    version: "1.0".to_string(),
                    description: "Block status transitions without verifiable evidence".to_string(),
                },
                Capability {
                    name: "preflight-validation".to_string(),
                    version: "1.0".to_string(),
                    description: "Pre-spawn agent precondition checks".to_string(),
                },
                Capability {
                    name: "workflow-automation".to_string(),
                    version: "1.0".to_string(),
                    description: "Thor auto-trigger, commit matching, stale reaper".to_string(),
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
        tracing::info!("evidence: starting workflow monitor");
        crate::workflow::spawn_workflow_monitor(self.pool.clone());
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM task_evidence", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "task_evidence table inaccessible".into(),
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
        let queries: &[(&str, &str)] = &[
            (
                "evidence.records.total",
                "SELECT COUNT(*) FROM task_evidence",
            ),
            (
                "evidence.stale_notifications.active",
                "SELECT COUNT(*) FROM stale_task_notifications WHERE resolved=0",
            ),
        ];
        queries
            .iter()
            .filter_map(|(name, sql)| {
                conn.query_row(sql, [], |r| r.get::<_, f64>(0))
                    .ok()
                    .map(|n| Metric {
                        name: (*name).into(),
                        value: n,
                        labels: vec![],
                    })
            })
            .collect()
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![ScheduledTask {
            name: "workflow-monitor",
            cron: "*/5 * * * *",
        }]
    }
}
