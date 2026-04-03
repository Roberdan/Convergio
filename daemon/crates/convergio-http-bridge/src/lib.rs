//! convergio-http-bridge — HTTP Extension bridge for Convergio.
//!
//! Allows external extensions (any language) to register with the daemon
//! via REST API and participate in the extension lifecycle:
//! register → health check → active → degraded → removed.
//!
//! Features:
//! - POST /api/extensions/register for external extension registration
//! - Background health check polling
//! - Event webhook delivery (domain events → POST to extension webhook)
//! - Route proxy under declared prefix (/api/ext/:id/*)

pub mod ext;
pub mod handlers;
pub mod health;
pub mod proxy;
pub mod schema;
pub mod store;
pub mod types;
pub mod webhook;

pub use ext::HttpBridgeExtension;
