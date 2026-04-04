// OrchestratorExtension — impl Extension for the orchestrator module.

use std::sync::Arc;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

pub struct OrchestratorExtension {
    pool: ConnPool,
    notify: Arc<Notify>,
}

impl OrchestratorExtension {
    pub fn new(pool: ConnPool, notify: Arc<Notify>) -> Self {
        Self { pool, notify }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }
}

impl Extension for OrchestratorExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-orchestrator".to_string(),
            description: "Plans, tasks, waves, Thor gate, reaper".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "plan-management".to_string(),
                    version: "1.0".to_string(),
                    description: "Create and manage execution plans".to_string(),
                },
                Capability {
                    name: "task-orchestration".to_string(),
                    version: "1.0".to_string(),
                    description: "Task lifecycle, wave progression, delegation".to_string(),
                },
                Capability {
                    name: "validation".to_string(),
                    version: "1.0".to_string(),
                    description: "Thor gate validation queue".to_string(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        let mut m = crate::schema::migrations();
        m.extend(crate::schema_tracking::tracking_migrations());
        m
    }

    fn routes(&self, ctx: &AppContext) -> Option<axum::Router> {
        let sink = ctx.get_arc::<Arc<dyn convergio_types::events::DomainEventSink>>();
        let state = Arc::new(crate::plan_routes::PlanState {
            pool: self.pool.clone(),
            event_sink: sink.map(|s| (*s).clone()),
            notify: self.notify.clone(),
        });
        let router = crate::scaffold::scaffold_routes()
            .merge(crate::plan_routes::plan_routes(Arc::clone(&state)))
            .merge(crate::plan_routes_ext::plan_routes_ext(Arc::clone(&state)))
            .merge(crate::plan_validate::validate_routes(Arc::clone(&state)))
            .merge(crate::task_routes::task_routes(state))
            .merge(crate::tracking_routes::tracking_routes(self.pool.clone()))
            .merge(crate::pm_routes::pm_routes(self.pool.clone()))
            .merge(crate::aggregation_routes::aggregation_routes(
                self.pool.clone(),
            ));
        Some(router)
    }

    fn on_start(&self, ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("orchestrator: starting reactor, validator, reaper");

        // Spawn Ali reactor with event sink for domain events
        let pool = self.pool.clone();
        let notify = self.notify.clone();
        let sink = ctx
            .get_arc::<Arc<dyn convergio_types::events::DomainEventSink>>()
            .map(|s| (*s).clone());
        tokio::spawn(async move {
            crate::reactor::run(pool, notify, sink).await;
        });

        // Spawn validator loop
        crate::validator::spawn_validator_loop(self.pool.clone());

        // Spawn reaper
        crate::reaper::spawn_reaper(self.pool.clone());

        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM plans", [], |r| r.get::<_, i64>(0))
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "plans table inaccessible".into(),
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
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM plans", [], |r| r.get::<_, f64>(0)) {
            metrics.push(Metric {
                name: "orchestrator.plans.total".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM tasks WHERE status='in_progress'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "orchestrator.tasks.active".into(),
                value: n,
                labels: vec![],
            });
        }
        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM validation_queue WHERE status='pending'",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            metrics.push(Metric {
                name: "orchestrator.validations.pending".into(),
                value: n,
                labels: vec![],
            });
        }
        metrics
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![
            ScheduledTask {
                name: "reaper",
                cron: "*/5 * * * *",
            },
            ScheduledTask {
                name: "validator",
                cron: "* * * * *",
            },
        ]
    }
}
