//! convergio-multitenancy — Multi-tenancy & org isolation hardening.
//!
//! Provides five isolation layers:
//! - DB isolation: per-org table prefixes, cross-org access blocked
//! - Network isolation: per-org peer whitelist for mesh sync
//! - Secret isolation: per-org keychain scoping
//! - Audit isolation: per-org audit trail, admin sees all
//! - Resource limits: per-org soft tracking (CPU, memory, storage, agents, API rate)

pub mod audit_isolation;
pub mod db_isolation;
pub mod ext;
pub mod network_isolation;
pub mod resource_limits;
pub mod routes;
pub mod schema;
pub mod secret_isolation;
pub mod types;

pub use ext::MultitenancyExtension;
