//! convergio-agents — Agent catalog, org routing, model preferences.
//!
//! Implements Extension: provides agent management and assignment.

pub mod ext;
pub mod routes;
pub mod schema;
pub mod seed;
pub mod store;
pub mod types;

pub use ext::AgentsCatalogExtension;
