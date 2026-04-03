//! ObservatoryExtension — impl Extension for the observatory module.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::routes::ObservatoryState;

/// The observatory extension — aggregated observability for the daemon.
pub struct ObservatoryExtension {
    pool: ConnPool,
}

impl ObservatoryExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn state(&self) -> Arc<ObservatoryState> {
        Arc::new(ObservatoryState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for ObservatoryExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-observatory".to_string(),
            description: "Observability aggregation — timeline, search, \
                          dashboards, anomaly detection, export"
                .into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "timeline".to_string(),
                    version: "1.0".to_string(),
                    description: "Cross-org event chronology with filters".into(),
                },
                Capability {
                    name: "full-text-search".to_string(),
                    version: "1.0".to_string(),
                    description: "FTS5 search across events and messages".into(),
                },
                Capability {
                    name: "dashboard-aggregates".to_string(),
                    version: "1.0".to_string(),
                    description: "Cost/hour, throughput/day, model latency".into(),
                },
                Capability {
                    name: "anomaly-detection".to_string(),
                    version: "1.0".to_string(),
                    description: "Cost spikes, throughput drops, idle agents".into(),
                },
                Capability {
                    name: "prometheus-export".to_string(),
                    version: "1.0".to_string(),
                    description: "Prometheus/Grafana metrics exposition".into(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::observatory_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("observatory: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM obs_timeline", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "obs_timeline table inaccessible".into(),
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

        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM obs_timeline", [], |r| {
            r.get::<_, f64>(0)
        }) {
            out.push(Metric {
                name: "observatory.timeline.total_events".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM obs_anomalies WHERE resolved = 0",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "observatory.anomalies.unresolved".into(),
                value: n,
                labels: vec![],
            });
        }

        out
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![ScheduledTask {
            name: "anomaly_scan",
            cron: "*/15 * * * *",
        }]
    }
}
