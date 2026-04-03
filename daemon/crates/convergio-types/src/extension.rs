//! The Extension trait — the only way to exist in Convergio.
//!
//! Every module (core or plugin) implements this trait.
//! No alternative, no workaround. If you don't implement Extension, you don't exist.

use crate::events::{DomainEvent, EventFilter};
use crate::manifest::Manifest;

/// Result type used across all extensions.
pub type ExtResult<T> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

/// A database migration owned by a module.
pub struct Migration {
    /// Monotonically increasing version number for this module.
    pub version: u32,
    /// Human-readable description.
    pub description: &'static str,
    /// SQL to apply (forward only for now).
    pub up: &'static str,
}

/// Health status reported by each extension.
#[derive(Debug, Clone, serde::Serialize)]
pub enum Health {
    Ok,
    Degraded { reason: String },
    Down { reason: String },
}

/// A named metric emitted by an extension.
#[derive(Debug, Clone, serde::Serialize)]
pub struct Metric {
    pub name: String,
    pub value: f64,
    pub labels: Vec<(String, String)>,
}

/// A scheduled task declared by an extension.
pub struct ScheduledTask {
    pub name: &'static str,
    /// Cron expression (e.g. "0 2 * * *" for 2 AM daily).
    pub cron: &'static str,
}

/// The one trait to rule them all.
///
/// Implement this to register your module with the Convergio daemon.
/// The daemon calls these methods at startup and runtime.
pub trait Extension: Send + Sync {
    /// Identity and capabilities — who you are, what you do.
    fn manifest(&self) -> Manifest;

    /// Your database tables. The migration runner applies these at startup,
    /// tracked in `_schema_registry`.
    fn migrations(&self) -> Vec<Migration> {
        vec![]
    }

    /// Your HTTP routes. The server mounts these under the appropriate prefix.
    fn routes(&self, ctx: &AppContext) -> Option<axum::Router> {
        let _ = ctx;
        None
    }

    /// Called once after migrations and before routes are served.
    fn on_start(&self, ctx: &AppContext) -> ExtResult<()> {
        let _ = ctx;
        Ok(())
    }

    /// Called on graceful shutdown.
    fn on_shutdown(&self) -> ExtResult<()> {
        Ok(())
    }

    /// Health check — aggregated into `/health/deep`.
    fn health(&self) -> Health {
        Health::Ok
    }

    /// Metrics — collected by the telemetry system.
    fn metrics(&self) -> Vec<Metric> {
        vec![]
    }

    /// Domain events this extension subscribes to.
    fn subscriptions(&self) -> Vec<EventFilter> {
        vec![]
    }

    /// Called when a subscribed domain event fires.
    fn on_event(&self, event: &DomainEvent) {
        let _ = event;
    }

    /// Periodic tasks (cron-like).
    fn scheduled_tasks(&self) -> Vec<ScheduledTask> {
        vec![]
    }

    /// Called when configuration changes at runtime.
    fn on_config_change(&self, key: &str, value: &serde_json::Value) -> ExtResult<()> {
        let _ = (key, value);
        Ok(())
    }
}

/// Shared application context passed to extensions.
///
/// Contains the database pool, event bus handle, and configuration.
/// Extensions receive this at startup and when building routes.
#[derive(Default)]
pub struct AppContext {
    // Will hold: db pool, event bus sender, config, telemetry handle
    // Filled in during Fase 2-3 when convergio-db and convergio-telemetry exist.
    _placeholder: (),
}

impl AppContext {
    pub fn new() -> Self {
        Self::default()
    }
}
