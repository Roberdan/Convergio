//! convergio-backup — Data retention, backup & disaster recovery.
//!
//! Provides retention policies with auto-purge, periodic SQLite snapshots
//! with WAL checkpoint, disaster recovery via snapshot restore, and
//! org-level data export/import for cross-node migration.
//!
//! Deps: types, db, security (audit trail), telemetry.

pub mod export;
pub mod ext;
pub mod import;
pub mod restore;
pub mod retention;
pub mod routes;
pub mod schema;
pub mod snapshot;
pub mod types;

pub use ext::BackupExtension;
pub use types::{BackupError, BackupResult};
