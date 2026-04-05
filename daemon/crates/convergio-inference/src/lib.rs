//! convergio-inference — Model routing, budget tracking, token optimization.
//!
//! Implements Extension: provides semantic model routing that replaces
//! static fallback chains with intelligent, budget-aware selection.

pub mod backend;
pub mod backend_mlx;
pub mod budget;
pub mod classifier;
pub mod ext;
pub mod metrics;
pub mod model_config;
pub mod router;
pub mod routes;
pub mod schema;
pub mod types;

pub use ext::InferenceExtension;
