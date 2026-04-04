//! Extension trait implementation for convergio-kernel (Jarvis).

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{AppContext, Extension, Health, Metric, Migration, ScheduledTask};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};
use tokio::sync::RwLock;

use crate::engine::KernelEngine;
use crate::routes::{KernelState, kernel_routes};

/// Kernel extension — Jarvis: local LLM assistant with monitoring and recovery.
pub struct KernelExtension {
    pool: ConnPool,
    #[allow(dead_code)]
    engine: Arc<RwLock<KernelEngine>>,
}

impl KernelExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self {
            pool,
            engine: Arc::new(RwLock::new(KernelEngine::default())),
        }
    }

    fn state(&self) -> Arc<KernelState> {
        Arc::new(KernelState {
            pool: self.pool.clone(),
            engine: RwLock::new(KernelEngine::default()),
        })
    }
}

impl Extension for KernelExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-kernel".to_string(),
            description: "Jarvis — local LLM inference, health monitoring, evidence gate, \
                          voice routing, Telegram notifications"
                .to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Extension,
            provides: vec![
                Capability {
                    name: "local-inference".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Local LLM inference via MLX (Qwen)".to_string(),
                },
                Capability {
                    name: "health-monitoring".to_string(),
                    version: "1.0.0".to_string(),
                    description: "30s health check cycle with recovery".to_string(),
                },
                Capability {
                    name: "evidence-gate".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Task completion verification (Article VI)".to_string(),
                },
                Capability {
                    name: "voice-routing".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Voice intent classification and routing".to_string(),
                },
            ],
            requires: vec![
                Dependency {
                    capability: "db-pool".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
                Dependency {
                    capability: "ipc-bus".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
                Dependency {
                    capability: "tts".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: false,
                },
            ],
            agent_tools: vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(kernel_routes(self.state()))
    }

    fn migrations(&self) -> Vec<Migration> {
        vec![
            Migration {
                version: 1,
                description: "kernel_events table",
                up: "CREATE TABLE IF NOT EXISTS kernel_events (\
                        id INTEGER PRIMARY KEY,\
                        timestamp TEXT DEFAULT (datetime('now')),\
                        severity TEXT CHECK(severity IN ('ok','warn','critical')),\
                        source TEXT,\
                        message TEXT,\
                        action_taken TEXT\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_ke_severity \
                        ON kernel_events(severity);\
                    CREATE INDEX IF NOT EXISTS idx_ke_ts \
                        ON kernel_events(timestamp);",
            },
            Migration {
                version: 2,
                description: "kernel_verifications table",
                up: "CREATE TABLE IF NOT EXISTS kernel_verifications (\
                        id INTEGER PRIMARY KEY,\
                        task_id INTEGER,\
                        timestamp TEXT DEFAULT (datetime('now')),\
                        checks_json TEXT,\
                        passed INTEGER,\
                        blocked_reason TEXT\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_kv_task \
                        ON kernel_verifications(task_id);",
            },
            Migration {
                version: 3,
                description: "kernel_config table",
                up: "CREATE TABLE IF NOT EXISTS kernel_config (\
                        key TEXT PRIMARY KEY,\
                        value TEXT,\
                        updated_at TEXT DEFAULT (datetime('now'))\
                    );",
            },
            Migration {
                version: 4,
                description: "knowledge_base table",
                up: "CREATE TABLE IF NOT EXISTS knowledge_base (\
                        id INTEGER PRIMARY KEY,\
                        domain TEXT,\
                        title TEXT,\
                        content TEXT,\
                        created_at TEXT,\
                        hit_count INTEGER DEFAULT 0\
                    );",
            },
        ]
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(_) => Health::Ok,
            Err(e) => Health::Degraded {
                reason: format!("db: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        vec![Metric {
            name: "kernel_active".to_string(),
            value: 1.0,
            labels: vec![],
        }]
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![
            ScheduledTask {
                name: "kernel-monitor",
                cron: "*/30 * * * * *",
            },
            ScheduledTask {
                name: "kernel-readiness",
                cron: "*/5 * * * *",
            },
        ]
    }
}
