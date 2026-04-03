//! convergio-server — Axum routing shell, extension wiring, middleware.
//!
//! Collects Extension::routes() from all registered extensions,
//! applies middleware (auth, audit, telemetry, rate-limit, CORS),
//! serves the unified API. Zero business logic — that lives in crates.

pub mod config;
pub mod config_defaults;
pub mod config_validation;
pub mod config_watcher;
pub mod middleware_audit;
pub mod middleware_auth;
pub mod middleware_telemetry;
pub mod rate_limiter;
pub mod router;
pub mod runner;
pub mod state;

pub use config::{config_path, load_config, write_default_config};
pub use router::build_router;
pub use runner::run_server;
pub use state::ServerState;
