//! convergio-inference — Model routing, budget tracking, token optimization.
//!
//! Implements Extension: provides semantic model routing that replaces
//! static fallback chains with intelligent, budget-aware selection.

pub mod budget;
pub mod classifier;
pub mod ext;
pub mod metrics;
pub mod router;
pub mod routes;
pub mod schema;
pub mod types;

pub use ext::InferenceExtension;
