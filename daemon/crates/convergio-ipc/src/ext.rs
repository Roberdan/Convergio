use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_telemetry::health::{ComponentHealth, HealthCheck};
use convergio_telemetry::metrics::MetricSource;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};
use tokio::sync::Notify;

use crate::sse::EventBus;
use crate::types::IpcStats;

pub struct IpcExtension {
    pool: ConnPool,
    notify: Arc<Notify>,
    event_bus: Arc<EventBus>,
    rate_limit: u32,
}

impl IpcExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self {
            pool,
            notify: Arc::new(Notify::new()),
            event_bus: Arc::new(EventBus::new(1024)),
            rate_limit: crate::messaging::DEFAULT_RATE_LIMIT,
        }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    pub fn notify(&self) -> &Arc<Notify> {
        &self.notify
    }

    pub fn event_bus(&self) -> &Arc<EventBus> {
        &self.event_bus
    }

    pub fn rate_limit(&self) -> u32 {
        self.rate_limit
    }

    pub fn set_rate_limit(&mut self, limit: u32) {
        self.rate_limit = limit;
    }

    pub fn stats(&self) -> Result<IpcStats, crate::types::IpcError> {
        let conn = self.pool.get()?;
        let agents: u64 = conn.query_row("SELECT count(*) FROM ipc_agents", [], |r| r.get(0))?;
        let messages: u64 =
            conn.query_row("SELECT count(*) FROM ipc_messages", [], |r| r.get(0))?;
        let channels: u64 =
            conn.query_row("SELECT count(*) FROM ipc_channels", [], |r| r.get(0))?;
        let context_keys: u64 =
            conn.query_row("SELECT count(*) FROM ipc_shared_context", [], |r| r.get(0))?;
        Ok(IpcStats {
            agents,
            messages,
            channels,
            context_keys,
        })
    }
}

impl Extension for IpcExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-ipc".into(),
            description: "Message bus, SSE streaming, agent registry".into(),
            version: "0.1.0".into(),
            kind: ModuleKind::Core,
            provides: vec![
                Capability {
                    name: "ipc-bus".into(),
                    version: "0.1.0".into(),
                    description: "Agent-to-agent messaging with channels".into(),
                },
                Capability {
                    name: "sse-events".into(),
                    version: "0.1.0".into(),
                    description: "Real-time event streaming via SSE".into(),
                },
                Capability {
                    name: "agent-registry".into(),
                    version: "0.1.0".into(),
                    description: "Agent registration and discovery".into(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn health(&self) -> Health {
        match self.stats() {
            Ok(_) => Health::Ok,
            Err(e) => Health::Degraded {
                reason: format!("IPC stats failed: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        match self.stats() {
            Ok(s) => vec![
                Metric {
                    name: "ipc_agents".into(),
                    value: s.agents as f64,
                    labels: vec![],
                },
                Metric {
                    name: "ipc_messages".into(),
                    value: s.messages as f64,
                    labels: vec![],
                },
                Metric {
                    name: "ipc_channels".into(),
                    value: s.channels as f64,
                    labels: vec![],
                },
            ],
            Err(_) => vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::event_routes(self.event_bus.clone()))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("IPC extension started");
        Ok(())
    }

    fn on_shutdown(&self) -> ExtResult<()> {
        tracing::info!("IPC extension shutdown");
        Ok(())
    }
}

impl HealthCheck for IpcExtension {
    fn name(&self) -> &str {
        "ipc"
    }

    fn check(&self) -> ComponentHealth {
        let (status, message) = match self.stats() {
            Ok(s) => (
                Health::Ok,
                Some(format!("{} agents, {} msgs", s.agents, s.messages)),
            ),
            Err(e) => (
                Health::Degraded {
                    reason: e.to_string(),
                },
                None,
            ),
        };
        ComponentHealth {
            name: "ipc".into(),
            status,
            message,
        }
    }
}

impl MetricSource for IpcExtension {
    fn name(&self) -> &str {
        "ipc"
    }

    fn collect(&self) -> Vec<Metric> {
        self.metrics()
    }
}
