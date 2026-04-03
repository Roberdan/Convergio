//! convergio-depgraph — Dependency graph validation, OpenAPI, capability listing.
//!
//! Validates the extension dependency graph at startup (fail-fast on cycles or
//! missing deps), blocks unsafe module removal, checks SemVer compatibility,
//! generates OpenAPI specs from Extension::routes(), and lists all capabilities.

pub mod ext;
pub mod graph;
pub mod openapi;
pub mod removal;
pub mod routes;
pub mod semver_check;

pub use ext::DepgraphExtension;
pub use graph::DepGraph;
