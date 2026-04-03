//! convergio-observatory — Observability aggregation layer.
//!
//! Aggregates data from every crate into a unified observability surface:
//! timeline, full-text search, dashboard aggregates, anomaly detection,
//! and export for Prometheus/Grafana/webhooks.

pub mod anomaly;
pub mod dashboard;
pub mod export;
pub mod ext;
pub mod routes;
pub mod routes_webhook;
pub mod schema;
pub mod search;
pub mod timeline;
pub mod types;

#[cfg(test)]
mod timeline_tests;

pub use ext::ObservatoryExtension;
