//! BillingExtension — impl Extension for the billing module.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::routes::BillingState;

/// The billing extension — metering, budgets, invoices, inter-org economics.
pub struct BillingExtension {
    pool: ConnPool,
}

impl BillingExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn state(&self) -> Arc<BillingState> {
        Arc::new(BillingState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for BillingExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-billing".to_string(),
            description: "Billing, metering, inter-org economics".into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "metering".to_string(),
                    version: "1.0".to_string(),
                    description: "Per-agent/task/org cost tracking".into(),
                },
                Capability {
                    name: "budget-hierarchy".to_string(),
                    version: "1.0".to_string(),
                    description: "Platform -> org -> agent budget enforcement".into(),
                },
                Capability {
                    name: "inter-org-billing".to_string(),
                    version: "1.0".to_string(),
                    description: "Rate cards and delegation cost tracking".into(),
                },
                Capability {
                    name: "invoicing".to_string(),
                    version: "1.0".to_string(),
                    description: "Periodic invoice generation per org".into(),
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
        Some(crate::routes::billing_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("billing: extension started");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM billing_usage", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "billing_usage table inaccessible".into(),
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

        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM billing_usage", [], |r| {
            r.get::<_, f64>(0)
        }) {
            out.push(Metric {
                name: "billing.usage.total_records".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(cost) = conn.query_row(
            "SELECT COALESCE(SUM(cost_usd), 0.0) FROM billing_usage
             WHERE date(created_at) = date('now')",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "billing.cost.today_usd".into(),
                value: cost,
                labels: vec![],
            });
        }

        out
    }
}
