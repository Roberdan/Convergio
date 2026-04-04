//! SchedulerExtension — impl Extension for the scheduler module.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::routes::SchedulerState;

/// The scheduler extension — policy-based task assignment.
pub struct SchedulerExtension {
    pool: ConnPool,
}

impl SchedulerExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    fn state(&self) -> Arc<SchedulerState> {
        Arc::new(SchedulerState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for SchedulerExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-scheduler".to_string(),
            description: "Policy-based task scheduling with capability matching".into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![Capability {
                name: "scheduling-policy".to_string(),
                version: "1.0".to_string(),
                description: "Intelligent task assignment to mesh peers".into(),
            }],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::scheduler_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("scheduler: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM scheduler_policies", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "scheduler_policies table inaccessible".into(),
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
        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM scheduling_decisions", [], |r| {
            r.get::<_, f64>(0)
        }) {
            out.push(Metric {
                name: "scheduler.decisions.total".into(),
                value: n,
                labels: vec![],
            });
        }
        out
    }
}
