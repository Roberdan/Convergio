//! convergio-db — Database pool, migration runner, schema registry.
//!
//! Provides r2d2 pool, collects migrations from all extensions,
//! tracks applied versions in `_schema_registry`.

pub mod core_tables;
pub mod ext;
pub mod helpers;
pub mod migration;
pub mod pool;

pub use ext::DbExtension;
