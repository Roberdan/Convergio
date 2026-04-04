//! Types for the node capability registry.

use serde::{Deserialize, Serialize};
use std::fmt;
use std::str::FromStr;

/// A single capability declared by a node.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NodeCapability {
    pub name: String,
    pub version: String,
    pub tags: Vec<String>,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

/// Well-known capability tags for routing decisions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CapabilityTag {
    Gpu,
    Voice,
    Compute,
    Storage,
    HighMemory,
    LowLatency,
    Inference,
    CodeExecution,
}

impl fmt::Display for CapabilityTag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let s = match self {
            Self::Gpu => "gpu",
            Self::Voice => "voice",
            Self::Compute => "compute",
            Self::Storage => "storage",
            Self::HighMemory => "high_memory",
            Self::LowLatency => "low_latency",
            Self::Inference => "inference",
            Self::CodeExecution => "code_execution",
        };
        f.write_str(s)
    }
}

impl FromStr for CapabilityTag {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "gpu" => Ok(Self::Gpu),
            "voice" => Ok(Self::Voice),
            "compute" => Ok(Self::Compute),
            "storage" => Ok(Self::Storage),
            "high_memory" => Ok(Self::HighMemory),
            "low_latency" => Ok(Self::LowLatency),
            "inference" => Ok(Self::Inference),
            "code_execution" => Ok(Self::CodeExecution),
            _ => Err(format!("unknown capability tag: {s}")),
        }
    }
}

/// All capabilities for a single peer.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NodeCapabilities {
    pub peer_name: String,
    pub capabilities: Vec<NodeCapability>,
    pub last_updated: String,
}

/// Query to find peers with specific capability tags.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityQuery {
    pub required_tags: Vec<CapabilityTag>,
    #[serde(default)]
    pub min_version: Option<String>,
}

/// Result of a capability query: peer with match score.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityMatch {
    pub peer_name: String,
    pub score: f64,
    pub matched_capabilities: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn capability_tag_display_and_parse() {
        let tags = [
            CapabilityTag::Gpu,
            CapabilityTag::Voice,
            CapabilityTag::Compute,
            CapabilityTag::Storage,
            CapabilityTag::HighMemory,
            CapabilityTag::LowLatency,
            CapabilityTag::Inference,
            CapabilityTag::CodeExecution,
        ];
        for tag in &tags {
            let s = tag.to_string();
            let parsed: CapabilityTag = s.parse().unwrap();
            assert_eq!(*tag, parsed);
        }
    }

    #[test]
    fn capability_tag_unknown_fails() {
        let result = "unknown_tag".parse::<CapabilityTag>();
        assert!(result.is_err());
    }

    #[test]
    fn node_capability_serde_roundtrip() {
        let cap = NodeCapability {
            name: "llm-inference".into(),
            version: "2.1.0".into(),
            tags: vec!["gpu".into(), "inference".into()],
            metadata: serde_json::json!({"model": "claude-opus"}),
        };
        let json = serde_json::to_string(&cap).unwrap();
        let parsed: NodeCapability = serde_json::from_str(&json).unwrap();
        assert_eq!(cap, parsed);
    }

    #[test]
    fn capability_query_serde_roundtrip() {
        let query = CapabilityQuery {
            required_tags: vec![CapabilityTag::Gpu, CapabilityTag::Inference],
            min_version: Some("1.0.0".into()),
        };
        let json = serde_json::to_string(&query).unwrap();
        let parsed: CapabilityQuery = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.required_tags.len(), 2);
        assert_eq!(parsed.min_version, Some("1.0.0".into()));
    }
}
