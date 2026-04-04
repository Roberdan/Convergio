//! convergio-mesh — Peer discovery, delta sync, delegation tracking.
//!
//! Implements Extension: owns mesh_sync_stats, peer_heartbeats,
//! host_heartbeats, mesh_peer_state, coordinator_events, delegation_progress.

pub mod auth;
pub mod convergence;
pub mod delegation;
pub mod error;
pub mod ext;
pub mod peers_parser;
pub mod peers_registry;
pub mod peers_types;
pub mod routes;
pub mod schema;
pub mod sync;
pub mod sync_apply;
pub mod transport;
pub mod types;
