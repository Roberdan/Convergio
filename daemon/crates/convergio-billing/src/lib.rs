//! convergio-billing — Billing, metering & inter-org economics.
//!
//! Tracks every cost-generating action at per-agent/task/org granularity.
//! Budget hierarchy: platform -> org -> agent. Inter-org billing via rate cards.
//! Tamper-evident audit trail with hash chain.

pub mod alerts;
pub mod audit;
pub mod budget;
pub mod ext;
pub mod invoices;
pub mod metering;
pub mod rates;
pub mod routes;
pub mod schema;
pub mod settlement;
pub mod types;

pub use ext::BillingExtension;
