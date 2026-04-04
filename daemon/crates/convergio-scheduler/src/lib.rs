//! convergio-scheduler — Policy-based task scheduling.
//!
//! Scores mesh peers by capability match, cost, load, and locality,
//! then assigns tasks to the best candidate using configurable weights.

pub mod ext;
pub mod policy;
pub mod routes;
pub mod schema;
pub mod types;

pub use ext::SchedulerExtension;
