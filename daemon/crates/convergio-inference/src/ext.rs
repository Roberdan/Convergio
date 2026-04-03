//! InferenceExtension — impl Extension for the inference module.

use std::sync::Arc;

use tokio::sync::RwLock;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::metrics::MetricsCollector;
use crate::router::ModelRouter;
use crate::routes::InferenceState;

/// The inference extension — model routing, budget tracking, token optimization.
pub struct InferenceExtension {
    pool: ConnPool,
    router: Arc<RwLock<ModelRouter>>,
    metrics: Arc<RwLock<MetricsCollector>>,
}

impl InferenceExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self {
            pool,
            router: Arc::new(RwLock::new(ModelRouter::new())),
            metrics: Arc::new(RwLock::new(MetricsCollector::new())),
        }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    pub fn router(&self) -> &Arc<RwLock<ModelRouter>> {
        &self.router
    }

    pub fn metrics(&self) -> &Arc<RwLock<MetricsCollector>> {
        &self.metrics
    }

    /// Build the shared state for API routes.
    pub fn state(&self) -> Arc<InferenceState> {
        Arc::new(InferenceState {
            pool: self.pool.clone(),
            router: self.router.clone(),
            metrics: self.metrics.clone(),
        })
    }
}

impl Extension for InferenceExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-inference".to_string(),
            description: "Model routing, budget tracking, token optimization".into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "model-routing".to_string(),
                    version: "1.0".to_string(),
                    description: "Semantic model selection by tier, budget, health"
                        .to_string(),
                },
                Capability {
                    name: "token-tracking".to_string(),
                    version: "1.0".to_string(),
                    description: "Per-agent/org/plan cost aggregation".to_string(),
                },
                Capability {
                    name: "budget-enforcement".to_string(),
                    version: "1.0".to_string(),
                    description: "Automatic tier downgrade on budget pressure"
                        .to_string(),
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
        Some(crate::routes::inference_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("inference: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row(
                        "SELECT COUNT(*) FROM inference_costs",
                        [],
                        |r| r.get::<_, i64>(0),
                    )
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "inference_costs table inaccessible".into(),
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

        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM inference_costs",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "inference.requests.total".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(cost) = conn.query_row(
            "SELECT COALESCE(SUM(cost_usd), 0.0) FROM inference_costs
             WHERE date(created_at) = date('now')",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "inference.cost.today_usd".into(),
                value: cost,
                labels: vec![],
            });
        }

        out
    }
}
