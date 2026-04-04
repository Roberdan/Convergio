//! SecurityExtension — impl Extension for remote execution security.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::trust_routes::SecurityState;

/// Extension providing trust levels, secrets filtering, and sandbox policies.
pub struct SecurityExtension {
    pool: ConnPool,
}

impl SecurityExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    fn state(&self) -> Arc<SecurityState> {
        Arc::new(SecurityState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for SecurityExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-security".to_string(),
            description: "Auth, HMAC, crypto, audit, trust, sandbox".into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "trust-levels".to_string(),
                    version: "1.0".to_string(),
                    description: "Per-peer trust level management".into(),
                },
                Capability {
                    name: "secrets-filtering".to_string(),
                    version: "1.0".to_string(),
                    description: "Env var filtering by trust level".into(),
                },
                Capability {
                    name: "sandbox-policy".to_string(),
                    version: "1.0".to_string(),
                    description: "Resource limits for remote execution".into(),
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
        Some(crate::trust_routes::security_routes(self.state()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("security: extension started (trust + sandbox)");
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM peer_trust", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "peer_trust table inaccessible".into(),
                    }
                }
            }
            Err(e) => Health::Down {
                reason: format!("pool error: {e}"),
            },
        }
    }
}
