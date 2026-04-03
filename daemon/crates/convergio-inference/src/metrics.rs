//! Inference metrics — rolling windows with per-model stats.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Single observation recorded after an inference call.
#[derive(Debug, Clone)]
pub struct MetricsEntry {
    pub model: String,
    pub latency_ms: u64,
    pub tokens_used: u32,
    pub cost: f64,
    pub success: bool,
    pub timestamp: DateTime<Utc>,
}

/// Time window for metric queries.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TimeWindow {
    OneHour,
    TwentyFourHours,
    SevenDays,
}

impl TimeWindow {
    fn duration(self) -> chrono::Duration {
        match self {
            Self::OneHour => chrono::Duration::hours(1),
            Self::TwentyFourHours => chrono::Duration::hours(24),
            Self::SevenDays => chrono::Duration::days(7),
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Self::OneHour => "1h",
            Self::TwentyFourHours => "24h",
            Self::SevenDays => "7d",
        }
    }
}

/// Computed statistics for one model over a time window.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelMetrics {
    pub model: String,
    pub request_count: usize,
    pub error_rate: f64,
    pub latency_p50: u64,
    pub latency_p95: u64,
    pub avg_cost: f64,
    pub window_label: String,
}

/// Bounded in-memory store of inference observations.
pub struct MetricsCollector {
    entries: Vec<MetricsEntry>,
}

impl MetricsCollector {
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
        }
    }

    /// Append one observation and evict entries beyond 7-day retention.
    pub fn record(&mut self, entry: MetricsEntry) {
        self.entries.push(entry);
        let cutoff = Utc::now() - TimeWindow::SevenDays.duration();
        self.entries.retain(|e| e.timestamp >= cutoff);
    }

    /// Compute stats for `model` within `window`.
    pub fn metrics_for(&self, model: &str, window: TimeWindow) -> ModelMetrics {
        let cutoff = Utc::now() - window.duration();
        let relevant: Vec<&MetricsEntry> = self
            .entries
            .iter()
            .filter(|e| e.model == model && e.timestamp >= cutoff)
            .collect();

        compute_metrics(model.to_string(), &relevant, window)
    }

    /// Compute stats for every known model within `window`.
    pub fn all_metrics(&self, window: TimeWindow) -> Vec<ModelMetrics> {
        let cutoff = Utc::now() - window.duration();
        let mut models: Vec<String> = self
            .entries
            .iter()
            .filter(|e| e.timestamp >= cutoff)
            .map(|e| e.model.clone())
            .collect();
        models.sort();
        models.dedup();
        models
            .into_iter()
            .map(|m| self.metrics_for(&m, window))
            .collect()
    }
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

fn compute_metrics(model: String, entries: &[&MetricsEntry], window: TimeWindow) -> ModelMetrics {
    if entries.is_empty() {
        return ModelMetrics {
            model,
            request_count: 0,
            error_rate: 0.0,
            latency_p50: 0,
            latency_p95: 0,
            avg_cost: 0.0,
            window_label: window.label().to_string(),
        };
    }

    let count = entries.len();
    let errors = entries.iter().filter(|e| !e.success).count();
    let error_rate = errors as f64 / count as f64;

    let mut latencies: Vec<u64> = entries.iter().map(|e| e.latency_ms).collect();
    latencies.sort_unstable();

    let avg_cost = entries.iter().map(|e| e.cost).sum::<f64>() / count as f64;

    ModelMetrics {
        model,
        request_count: count,
        error_rate,
        latency_p50: percentile(&latencies, 50),
        latency_p95: percentile(&latencies, 95),
        avg_cost,
        window_label: window.label().to_string(),
    }
}

/// Nearest-rank percentile.
fn percentile(sorted: &[u64], p: usize) -> u64 {
    if sorted.is_empty() {
        return 0;
    }
    let idx = ((p as f64 / 100.0) * sorted.len() as f64).ceil() as usize;
    sorted[idx.saturating_sub(1).min(sorted.len() - 1)]
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entry(model: &str, latency: u64, cost: f64, success: bool) -> MetricsEntry {
        MetricsEntry {
            model: model.into(),
            latency_ms: latency,
            tokens_used: 100,
            cost,
            success,
            timestamp: Utc::now(),
        }
    }

    #[test]
    fn empty_collector_returns_zero_metrics() {
        let collector = MetricsCollector::new();
        let m = collector.metrics_for("haiku", TimeWindow::OneHour);
        assert_eq!(m.request_count, 0);
        assert_eq!(m.error_rate, 0.0);
    }

    #[test]
    fn records_and_computes_metrics() {
        let mut collector = MetricsCollector::new();
        collector.record(entry("opus", 200, 0.5, true));
        collector.record(entry("opus", 300, 0.6, true));
        collector.record(entry("opus", 500, 0.4, false));

        let m = collector.metrics_for("opus", TimeWindow::OneHour);
        assert_eq!(m.request_count, 3);
        assert!((m.error_rate - 1.0 / 3.0).abs() < 0.01);
        assert_eq!(m.latency_p50, 300);
    }

    #[test]
    fn all_metrics_returns_per_model() {
        let mut collector = MetricsCollector::new();
        collector.record(entry("haiku", 50, 0.01, true));
        collector.record(entry("opus", 200, 0.5, true));

        let all = collector.all_metrics(TimeWindow::OneHour);
        assert_eq!(all.len(), 2);
    }
}
