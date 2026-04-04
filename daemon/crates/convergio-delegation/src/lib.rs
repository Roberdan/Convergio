//! convergio-delegation — Delegation orchestrator for multi-node execution.
//!
//! Ties together file transport, capability matching, remote agent spawning,
//! monitoring, and sync-back into a complete delegation pipeline.

pub mod ext;
pub mod pipeline;
pub mod queries;
pub mod remote_spawn;
pub mod routes;
pub mod schema;
pub mod types;

pub use ext::DelegationExtension;
