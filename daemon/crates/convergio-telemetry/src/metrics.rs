//! Metrics collection — aggregates Metric from all extensions.

use convergio_types::extension::Metric;
use std::sync::{Arc, Mutex};

/// Collects metrics from all registered sources.
pub struct MetricsCollector {
    sources: Mutex<Vec<Arc<dyn MetricSource>>>,
}

/// Trait for anything that can provide metrics.
pub trait MetricSource: Send + Sync {
    fn name(&self) -> &str;
    fn collect(&self) -> Vec<Metric>;
}

impl MetricsCollector {
    pub fn new() -> Self {
        Self {
            sources: Mutex::new(Vec::new()),
        }
    }

    pub fn register(&self, source: Arc<dyn MetricSource>) {
        self.sources.lock().expect("metrics lock").push(source);
    }

    /// Collect metrics from all registered sources.
    pub fn collect_all(&self) -> Vec<Metric> {
        self.sources
            .lock()
            .expect("metrics lock")
            .iter()
            .flat_map(|s| s.collect())
            .collect()
    }
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct FakeSource;

    impl MetricSource for FakeSource {
        fn name(&self) -> &str {
            "fake"
        }
        fn collect(&self) -> Vec<Metric> {
            vec![Metric {
                name: "test_counter".to_string(),
                value: 42.0,
                labels: vec![("env".to_string(), "test".to_string())],
            }]
        }
    }

    #[test]
    fn collect_all_from_sources() {
        let collector = MetricsCollector::new();
        collector.register(Arc::new(FakeSource));
        let metrics = collector.collect_all();
        assert_eq!(metrics.len(), 1);
        assert_eq!(metrics[0].name, "test_counter");
        assert_eq!(metrics[0].value, 42.0);
    }

    #[test]
    fn empty_collector() {
        let collector = MetricsCollector::new();
        assert!(collector.collect_all().is_empty());
    }
}
