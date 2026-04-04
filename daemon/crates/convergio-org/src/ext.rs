//! Extension trait implementation for convergio-org.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

use crate::routes::{org_routes, OrgState};

/// Org extension — organization design, provisioning, notifications, decisions.
pub struct OrgExtension {
    pool: ConnPool,
}

impl OrgExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    fn state(&self) -> Arc<OrgState> {
        Arc::new(OrgState {
            pool: self.pool.clone(),
        })
    }
}

impl Extension for OrgExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-org".to_string(),
            description: "Organization chart, provisioning, notifications, decision log"
                .to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Extension,
            provides: vec![
                Capability {
                    name: "org-design".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Design orgs from mission statements or repo profiles".to_string(),
                },
                Capability {
                    name: "org-provisioning".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Provision orgs via daemon HTTP API".to_string(),
                },
                Capability {
                    name: "notification-queue".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Queue and deliver notifications with audit trail".to_string(),
                },
                Capability {
                    name: "decision-log".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Audit trail of agent decisions with reasoning".to_string(),
                },
            ],
            requires: vec![Dependency {
                capability: "db-pool".to_string(),
                version_req: ">=1.0.0".to_string(),
                required: true,
            }],
            agent_tools: vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(org_routes(self.state()))
    }

    fn migrations(&self) -> Vec<Migration> {
        vec![
            Migration {
                version: 1,
                description: "notifications table",
                up: "CREATE TABLE IF NOT EXISTS notifications (\
                        id INTEGER PRIMARY KEY AUTOINCREMENT,\
                        type TEXT NOT NULL DEFAULT '',\
                        title TEXT NOT NULL DEFAULT '',\
                        message TEXT NOT NULL DEFAULT '',\
                        is_read INTEGER DEFAULT 0,\
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\
                        updated_at DATETIME\
                    );",
            },
            Migration {
                version: 2,
                description: "notification_queue table",
                up: "CREATE TABLE IF NOT EXISTS notification_queue (\
                        id INTEGER PRIMARY KEY,\
                        severity TEXT DEFAULT 'info',\
                        title TEXT NOT NULL DEFAULT '',\
                        message TEXT,\
                        plan_id INTEGER,\
                        link TEXT,\
                        status TEXT DEFAULT 'pending',\
                        created_at TEXT DEFAULT (datetime('now')),\
                        delivered_at TEXT\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_nq_status \
                        ON notification_queue(status);",
            },
            Migration {
                version: 3,
                description: "notification_deliveries table",
                up: "CREATE TABLE IF NOT EXISTS notification_deliveries (\
                        id INTEGER PRIMARY KEY AUTOINCREMENT,\
                        notification_id INTEGER NOT NULL,\
                        trace_id TEXT NOT NULL,\
                        channel TEXT NOT NULL,\
                        success INTEGER NOT NULL DEFAULT 0,\
                        error_message TEXT,\
                        duration_ms INTEGER NOT NULL DEFAULT 0,\
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_nd_notification \
                        ON notification_deliveries(notification_id);\
                    CREATE INDEX IF NOT EXISTS idx_nd_trace \
                        ON notification_deliveries(trace_id);",
            },
            Migration {
                version: 4,
                description: "decision_log table",
                up: "CREATE TABLE IF NOT EXISTS decision_log (\
                        id INTEGER PRIMARY KEY,\
                        plan_id INTEGER,\
                        task_id INTEGER,\
                        decision TEXT NOT NULL,\
                        reasoning TEXT NOT NULL,\
                        first_principles TEXT,\
                        alternatives_considered TEXT,\
                        outcome TEXT,\
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\
                        agent TEXT\
                    );",
            },
        ]
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let count: i64 = conn
                    .query_row("SELECT count(*) FROM ipc_orgs", [], |r| r.get(0))
                    .unwrap_or(0);
                if count >= 0 {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "negative org count".into(),
                    }
                }
            }
            Err(e) => Health::Degraded {
                reason: format!("db: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let conn = match self.pool.get() {
            Ok(c) => c,
            Err(_) => return vec![],
        };
        let orgs: f64 = conn
            .query_row("SELECT count(*) FROM ipc_orgs", [], |r| r.get(0))
            .unwrap_or(0.0);
        let notifs: f64 = conn
            .query_row(
                "SELECT count(*) FROM notification_queue WHERE status = 'pending'",
                [],
                |r| r.get(0),
            )
            .unwrap_or(0.0);
        vec![
            Metric {
                name: "org_count".into(),
                value: orgs,
                labels: vec![],
            },
            Metric {
                name: "org_pending_notifications".into(),
                value: notifs,
                labels: vec![],
            },
        ]
    }
}
