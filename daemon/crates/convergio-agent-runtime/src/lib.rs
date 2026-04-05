//! convergio-agent-runtime — Agent runtime: memory model + concurrency.
//!
//! The daemon manages agents like a compiler manages memory:
//! allocation (spawn), ownership (org), borrowing (delegation),
//! lifetime (heartbeat), GC (reaper).
//!
//! Implements Extension: provides scheduling, isolation, and lifecycle
//! management for AI agents.

pub mod adaptation;
pub mod adaptation_routes;
pub mod allocator;
pub mod concurrency;
pub mod context;
pub mod context_routes;
pub mod delegation;
pub mod ext;
pub mod heartbeat;
pub mod monitor_helpers;
pub mod reaper;
pub mod respawn;
pub mod routes;
pub mod scheduler;
pub mod schema;
pub mod scope;
pub mod spawn_monitor;
pub mod spawn_routes;
pub mod spawner;
pub mod types;

pub use ext::AgentRuntimeExtension;
