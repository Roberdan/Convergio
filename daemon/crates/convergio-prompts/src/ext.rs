//! Extension trait implementation for convergio-prompts.

use convergio_db::pool::ConnPool;
use convergio_telemetry::health::{ComponentHealth, HealthCheck};
use convergio_telemetry::metrics::MetricSource;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// The prompts extension — prompt management and skill registry.
pub struct PromptsExtension {
    pool: ConnPool,
}

impl PromptsExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    fn prompt_count(&self) -> Result<u64, String> {
        let conn = self.pool.get().map_err(|e| e.to_string())?;
        let count: i64 = conn
            .query_row(
                "SELECT count(*) FROM prompt_templates WHERE active = 1",
                [],
                |r| r.get(0),
            )
            .map_err(|e| e.to_string())?;
        Ok(count as u64)
    }

    fn skill_count(&self) -> Result<u64, String> {
        let conn = self.pool.get().map_err(|e| e.to_string())?;
        let count: i64 = conn
            .query_row("SELECT count(*) FROM prompt_skills", [], |r| r.get(0))
            .map_err(|e| e.to_string())?;
        Ok(count as u64)
    }
}

impl Extension for PromptsExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-prompts".into(),
            description: "Prompt management, skill registry, A/B testing".into(),
            version: "0.1.0".into(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "prompt-templates".into(),
                    version: "0.1.0".into(),
                    description: "Versioned prompt templates with variable substitution".into(),
                },
                Capability {
                    name: "skill-registry".into(),
                    version: "0.1.0".into(),
                    description: "Agent skill declaration and discovery".into(),
                },
                Capability {
                    name: "prompt-ab-testing".into(),
                    version: "0.1.0".into(),
                    description: "A/B testing for prompt comparison".into(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        Some(crate::routes::routes(self.pool.clone()))
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn health(&self) -> Health {
        match (self.prompt_count(), self.skill_count()) {
            (Ok(_), Ok(_)) => Health::Ok,
            (Err(e), _) | (_, Err(e)) => Health::Degraded {
                reason: format!("prompts health check failed: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let mut metrics = vec![];
        if let Ok(n) = self.prompt_count() {
            metrics.push(Metric {
                name: "prompts_active_templates".into(),
                value: n as f64,
                labels: vec![],
            });
        }
        if let Ok(n) = self.skill_count() {
            metrics.push(Metric {
                name: "prompts_registered_skills".into(),
                value: n as f64,
                labels: vec![],
            });
        }
        metrics
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        let conn = self.pool.get().map_err(|e| e.to_string())?;
        if let Err(e) = crate::seed::run(&conn) {
            tracing::warn!("prompt seed failed: {e}");
        }
        // Seed workflow skills (solve, planner, execute, etc.)
        match crate::seed_skills::seed(&self.pool) {
            Ok(n) if n > 0 => tracing::info!(inserted = n, "workflow skills seeded"),
            Err(e) => tracing::warn!("skill seed failed: {e}"),
            _ => {}
        }
        tracing::info!("Prompts extension started");
        Ok(())
    }

    fn on_shutdown(&self) -> ExtResult<()> {
        tracing::info!("Prompts extension shutdown");
        Ok(())
    }
}

impl HealthCheck for PromptsExtension {
    fn name(&self) -> &str {
        "prompts"
    }

    fn check(&self) -> ComponentHealth {
        let (status, message) = match (self.prompt_count(), self.skill_count()) {
            (Ok(p), Ok(s)) => (Health::Ok, Some(format!("{p} templates, {s} skills"))),
            (Err(e), _) | (_, Err(e)) => (Health::Degraded { reason: e.clone() }, None),
        };
        ComponentHealth {
            name: "prompts".into(),
            status,
            message,
        }
    }
}

impl MetricSource for PromptsExtension {
    fn name(&self) -> &str {
        "prompts"
    }

    fn collect(&self) -> Vec<Metric> {
        self.metrics()
    }
}
