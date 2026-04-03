//! Configuration types — pure data structures, no I/O.
//!
//! Loading, validation, and hot-reload live elsewhere (server crate).
//! These structs are shared across crates for type-safe config access.

use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct NodeConfig {
    pub name: String,
    /// standalone | coordinator | worker
    pub role: String,
}

impl Default for NodeConfig {
    fn default() -> Self {
        Self {
            name: String::new(),
            role: "standalone".to_string(),
        }
    }
}

#[derive(Debug, Clone, Deserialize, Default)]
#[serde(default)]
pub struct TailscaleConfig {
    pub enabled: bool,
    pub auth_key: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct MeshConfig {
    pub transport: String,
    pub discovery: String,
    pub peers: Vec<String>,
    pub tailscale: TailscaleConfig,
}

impl Default for MeshConfig {
    fn default() -> Self {
        Self {
            transport: "lan".to_string(),
            discovery: "mdns".to_string(),
            peers: Vec::new(),
            tailscale: TailscaleConfig::default(),
        }
    }
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
#[serde(default)]
pub struct InferenceFallbackConfig {
    pub max_attempts: usize,
    pub t1: Vec<String>,
    pub t2: Vec<String>,
    pub t3: Vec<String>,
    pub t4: Vec<String>,
}

impl Default for InferenceFallbackConfig {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            t1: vec!["local".into(), "haiku".into(), "sonnet".into()],
            t2: vec!["haiku".into(), "local".into(), "sonnet".into()],
            t3: vec!["sonnet".into(), "opus".into()],
            t4: vec!["opus".into(), "sonnet".into()],
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct InferenceConfig {
    pub default_model: String,
    pub api_key_env: String,
    pub fallback: InferenceFallbackConfig,
}

impl Default for InferenceConfig {
    fn default() -> Self {
        Self {
            default_model: "claude-sonnet-4-6".to_string(),
            api_key_env: "ANTHROPIC_API_KEY".to_string(),
            fallback: InferenceFallbackConfig::default(),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct KernelConfig {
    pub model: String,
    pub model_path: String,
    pub escalation_model: String,
    pub max_tokens: u32,
}

impl Default for KernelConfig {
    fn default() -> Self {
        Self {
            model: "none".to_string(),
            model_path: String::new(),
            escalation_model: String::new(),
            max_tokens: 2048,
        }
    }
}

#[derive(Debug, Clone, Deserialize, Default)]
#[serde(default)]
pub struct TelegramConfig {
    pub enabled: bool,
    pub token_keychain: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct NightConfig {
    pub night_mode: bool,
    /// Format: "HH:MM-HH:MM" (e.g. "23:00-07:00")
    pub night_hours: String,
    pub night_model: String,
}

impl Default for NightConfig {
    fn default() -> Self {
        Self {
            night_mode: false,
            night_hours: "23:00-07:00".to_string(),
            night_model: "claude-haiku-4-5".to_string(),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(default)]
pub struct DaemonConfig {
    pub port: u16,
    pub quiet_hours: Option<String>,
    pub timezone: Option<String>,
    pub auto_update: bool,
}

impl Default for DaemonConfig {
    fn default() -> Self {
        Self {
            port: 8420,
            quiet_hours: None,
            timezone: None,
            auto_update: true,
        }
    }
}

/// Top-level config — deserialized from config.toml.
#[derive(Debug, Clone, Deserialize, Default)]
#[serde(default)]
pub struct ConvergioConfig {
    pub node: NodeConfig,
    pub daemon: DaemonConfig,
    pub night: NightConfig,
    pub mesh: MeshConfig,
    pub inference: InferenceConfig,
    pub kernel: KernelConfig,
    pub telegram: TelegramConfig,
}
