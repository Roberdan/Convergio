//! AgentRuntimeExtension — impl Extension for the agent runtime.

use std::sync::Arc;
use std::time::Duration;

use convergio_db::pool::ConnPool;
use convergio_types::extension::{
    AppContext, ExtResult, Extension, Health, Metric, Migration, ScheduledTask,
};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use crate::routes::{runtime_routes, RuntimeState};

/// The Extension entry point for the agent runtime.
pub struct AgentRuntimeExtension {
    pool: ConnPool,
}

impl AgentRuntimeExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn state(&self) -> Arc<RuntimeState> {
        Arc::new(RuntimeState {
            pool: self.pool.clone(),
        })
    }
}

impl Default for AgentRuntimeExtension {
    fn default() -> Self {
        let pool = convergio_db::pool::create_memory_pool().expect("in-memory pool for default");
        Self { pool }
    }
}

impl Extension for AgentRuntimeExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-agent-runtime".to_string(),
            description: "Agent runtime: allocation, isolation, ownership, \
                          scheduling, concurrency, reaper"
                .to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "agent-allocation".to_string(),
                    version: "1.0".to_string(),
                    description: "Spawn agents with budget, capability, model".to_string(),
                },
                Capability {
                    name: "workspace-isolation".to_string(),
                    version: "1.0".to_string(),
                    description: "Isolated workspace per agent, scope enforcement".to_string(),
                },
                Capability {
                    name: "agent-scheduling".to_string(),
                    version: "1.0".to_string(),
                    description: "Priority queue with fair cross-org scheduling".to_string(),
                },
                Capability {
                    name: "agent-delegation".to_string(),
                    version: "1.0".to_string(),
                    description: "Borrow agents across tasks/orgs with timeout".to_string(),
                },
                Capability {
                    name: "agent-reaper".to_string(),
                    version: "1.0".to_string(),
                    description: "GC for dead agents, orphan tasks, expired delegations"
                        .to_string(),
                },
                Capability {
                    name: "agent-context".to_string(),
                    version: "1.0".to_string(),
                    description: "Per-agent live context from DB".to_string(),
                },
                Capability {
                    name: "agent-adaptation".to_string(),
                    version: "1.0".to_string(),
                    description: "Live adaptation: poll updates, sentinel files".to_string(),
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
        // Determine repo root for worktree creation
        let repo_root = std::env::current_dir()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|_| ".".into());
        let daemon_url = std::env::var("CONVERGIO_DAEMON_URL")
            .unwrap_or_else(|_| "http://localhost:8420".into());
        let spawn_state = Arc::new(crate::spawn_routes::SpawnState {
            pool: self.pool.clone(),
            repo_root,
            daemon_url,
        });
        let ctx_state = Arc::new(crate::context_routes::ContextState {
            pool: self.pool.clone(),
        });
        let adapt_state = Arc::new(crate::adaptation_routes::AdaptationState {
            pool: self.pool.clone(),
        });
        let router = runtime_routes(self.state())
            .merge(crate::spawn_routes::spawn_routes(spawn_state))
            .merge(crate::context_routes::context_routes(ctx_state))
            .merge(crate::adaptation_routes::adaptation_routes(adapt_state));
        Some(router)
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("agent-runtime: starting reaper (60s interval)");
        let reaper_interval = Duration::from_secs(60);
        crate::reaper::spawn_reaper(self.pool.clone(), reaper_interval);
        Ok(())
    }

    fn health(&self) -> Health {
        match self.pool.get() {
            Ok(conn) => {
                let ok = conn
                    .query_row("SELECT COUNT(*) FROM art_agents", [], |r| {
                        r.get::<_, i64>(0)
                    })
                    .is_ok();
                if ok {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "art_agents table inaccessible".into(),
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
            "SELECT COUNT(*) FROM art_agents WHERE stage IN ('running','borrowed')",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "agent_runtime.agents.active".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(n) = conn.query_row("SELECT COUNT(*) FROM art_queue", [], |r| r.get::<_, f64>(0))
        {
            out.push(Metric {
                name: "agent_runtime.queue.depth".into(),
                value: n,
                labels: vec![],
            });
        }

        if let Ok(n) = conn.query_row(
            "SELECT COUNT(*) FROM art_delegations WHERE returned = 0",
            [],
            |r| r.get::<_, f64>(0),
        ) {
            out.push(Metric {
                name: "agent_runtime.delegations.active".into(),
                value: n,
                labels: vec![],
            });
        }

        out
    }

    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![ScheduledTask {
            name: "agent-reaper",
            cron: "* * * * *",
        }]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_correct_id() {
        let ext = AgentRuntimeExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-agent-runtime");
        assert_eq!(m.provides.len(), 7);
    }

    #[test]
    fn migrations_are_returned() {
        let ext = AgentRuntimeExtension::default();
        let migs = ext.migrations();
        assert_eq!(migs.len(), 4);
    }

    #[test]
    fn health_ok_with_memory_pool() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        drop(conn);
        let ext = AgentRuntimeExtension::new(pool);
        assert!(matches!(ext.health(), Health::Ok));
    }
}
