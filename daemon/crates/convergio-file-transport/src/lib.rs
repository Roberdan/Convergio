//! convergio-file-transport — Rsync-based file transport between mesh nodes.
//!
//! Provides rsync push/pull between peers, transfer tracking with audit
//! trail, HTTP API for triggering and querying transfers.

pub mod ext;
pub mod routes;
pub mod rsync;
pub mod schema;
pub mod transfer;
pub mod types;

pub use ext::FileTransportExtension;
