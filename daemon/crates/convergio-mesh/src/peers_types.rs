//! Peer configuration types for peers.conf INI format.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PeersError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("missing required field '{field}' in peer '{peer}'")]
    MissingField { peer: String, field: String },
    #[error("peer '{0}' not found")]
    NotFound(String),
    #[error("parse error at line {line}: {msg}")]
    Parse { line: usize, msg: String },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PeerConfig {
    pub ssh_alias: String,
    pub user: String,
    pub os: String,
    pub tailscale_ip: String,
    pub dns_name: String,
    pub capabilities: Vec<String>,
    pub role: String,
    pub status: String,
    pub thunderbolt_ip: Option<String>,
    pub lan_ip: Option<String>,
    pub mac_address: Option<String>,
    pub gh_account: Option<String>,
    pub runners: Option<u32>,
    pub runner_paths: Option<String>,
    #[serde(default)]
    pub aliases: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct PeersRegistry {
    pub shared_secret: String,
    pub peers: BTreeMap<String, PeerConfig>,
}
