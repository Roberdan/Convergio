//! convergio-types — The contract everything builds on.
//!
//! Defines the Extension trait, Manifest, DomainEvent, and shared types.
//! Every crate in the workspace depends on this.

pub mod config;
pub mod errors;
pub mod events;
pub mod extension;
pub mod manifest;
pub mod message_error;
pub mod platform_paths;
pub mod resilience;
