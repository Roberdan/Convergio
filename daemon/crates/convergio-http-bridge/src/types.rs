//! Types for HTTP extension bridge — registration, lifecycle, config.

use chrono::{DateTime, Utc};
use convergio_types::manifest::Manifest;

/// Lifecycle states for an HTTP extension.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BridgeState {
    /// Just registered, awaiting first health check.
    Registered,
    /// Health check passed, extension is serving.
    Active,
    /// Health check failed but not yet removed.
    Degraded,
    /// Explicitly removed or too many failures.
    Removed,
}

impl BridgeState {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Registered => "registered",
            Self::Active => "active",
            Self::Degraded => "degraded",
            Self::Removed => "removed",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "registered" => Some(Self::Registered),
            "active" => Some(Self::Active),
            "degraded" => Some(Self::Degraded),
            "removed" => Some(Self::Removed),
            _ => None,
        }
    }
}

/// Registration request from an external extension.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RegisterRequest {
    /// Unique extension ID (e.g. "openclaw-bridge").
    pub id: String,
    /// Semantic manifest — capabilities, deps, tools.
    pub manifest: Manifest,
    /// Base URL where the extension listens (e.g. "http://localhost:3100").
    pub base_url: String,
    /// Path for health checks (e.g. "/health").
    pub health_endpoint: String,
    /// Path for event webhook delivery (e.g. "/webhook/events").
    pub events_webhook: String,
    /// Route prefix mounted in the daemon (e.g. "/api/ext/openclaw").
    pub routes_prefix: String,
}

/// A registered HTTP extension record.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct HttpExtension {
    pub id: String,
    pub manifest: Manifest,
    pub base_url: String,
    pub health_endpoint: String,
    pub events_webhook: String,
    pub routes_prefix: String,
    pub state: BridgeState,
    pub registered_at: DateTime<Utc>,
    pub last_health_check: Option<DateTime<Utc>>,
    pub consecutive_failures: u32,
}

/// Maximum consecutive health check failures before removal.
pub const MAX_FAILURES: u32 = 5;

/// Default health check interval in seconds.
pub const HEALTH_CHECK_INTERVAL_SECS: u64 = 30;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bridge_state_roundtrip() {
        for state in [
            BridgeState::Registered,
            BridgeState::Active,
            BridgeState::Degraded,
            BridgeState::Removed,
        ] {
            let s = state.as_str();
            assert_eq!(BridgeState::parse(s), Some(state));
        }
        assert_eq!(BridgeState::parse("unknown"), None);
    }

    #[test]
    fn bridge_state_serde() {
        let json = serde_json::to_string(&BridgeState::Active).unwrap();
        assert_eq!(json, "\"active\"");
        let back: BridgeState = serde_json::from_str(&json).unwrap();
        assert_eq!(back, BridgeState::Active);
    }
}
