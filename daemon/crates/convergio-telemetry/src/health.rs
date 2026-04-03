//! Health check infrastructure — registry and aggregation.
//!
//! Uses the Health enum from convergio-types.
//! Extensions expose health via Extension::health().
//! Additional components implement HealthCheck trait.

use convergio_types::extension::Health;
use std::sync::{Arc, Mutex};

/// Point-in-time health snapshot for a single component.
#[derive(Debug, Clone)]
pub struct ComponentHealth {
    pub name: String,
    pub status: Health,
    pub message: Option<String>,
}

/// Trait for non-Extension components that expose health.
pub trait HealthCheck: Send + Sync {
    fn name(&self) -> &str;
    fn check(&self) -> ComponentHealth;
}

/// Thread-safe registry that aggregates health checks.
pub struct HealthRegistry {
    checks: Mutex<Vec<Arc<dyn HealthCheck>>>,
}

impl HealthRegistry {
    pub fn new() -> Self {
        Self {
            checks: Mutex::new(Vec::new()),
        }
    }

    pub fn register(&self, check: Arc<dyn HealthCheck>) {
        self.checks.lock().expect("registry lock").push(check);
    }

    /// Returns health snapshots for all registered components.
    pub fn check_all(&self) -> Vec<ComponentHealth> {
        self.checks
            .lock()
            .expect("registry lock")
            .iter()
            .map(|c| c.check())
            .collect()
    }

    /// Aggregate: any Down => Down, any Degraded => Degraded, else Ok.
    pub fn aggregate_status(&self) -> Health {
        let checks = self.check_all();
        if checks.iter().any(|c| matches!(c.status, Health::Down { .. })) {
            return Health::Down {
                reason: "one or more components down".to_string(),
            };
        }
        if checks.iter().any(|c| matches!(c.status, Health::Degraded { .. })) {
            return Health::Degraded {
                reason: "one or more components degraded".to_string(),
            };
        }
        Health::Ok
    }
}

impl Default for HealthRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Fake(Health);

    impl HealthCheck for Fake {
        fn name(&self) -> &str {
            "fake"
        }
        fn check(&self) -> ComponentHealth {
            ComponentHealth {
                name: "fake".to_string(),
                status: self.0.clone(),
                message: None,
            }
        }
    }

    #[test]
    fn all_healthy() {
        let reg = HealthRegistry::new();
        reg.register(Arc::new(Fake(Health::Ok)));
        reg.register(Arc::new(Fake(Health::Ok)));
        assert!(matches!(reg.aggregate_status(), Health::Ok));
    }

    #[test]
    fn one_degraded() {
        let reg = HealthRegistry::new();
        reg.register(Arc::new(Fake(Health::Ok)));
        reg.register(Arc::new(Fake(Health::Degraded {
            reason: "slow".into(),
        })));
        assert!(matches!(reg.aggregate_status(), Health::Degraded { .. }));
    }

    #[test]
    fn one_down() {
        let reg = HealthRegistry::new();
        reg.register(Arc::new(Fake(Health::Degraded {
            reason: "slow".into(),
        })));
        reg.register(Arc::new(Fake(Health::Down {
            reason: "dead".into(),
        })));
        assert!(matches!(reg.aggregate_status(), Health::Down { .. }));
    }

    #[test]
    fn check_all_count() {
        let reg = HealthRegistry::new();
        reg.register(Arc::new(Fake(Health::Ok)));
        reg.register(Arc::new(Fake(Health::Ok)));
        assert_eq!(reg.check_all().len(), 2);
    }
}
