//! Kernel engine — local LLM inference routing and classification.
//!
//! Wraps local MLX inference (Qwen) with cloud fallback (Claude Opus).
//! Classification is deterministic rule-based, inference routing is budget-aware.

use super::types::{InferenceLevel, KernelAction, KernelConfig, KernelSeverity, KernelStatus};

/// Core kernel engine — manages model state and inference routing.
pub struct KernelEngine {
    config: KernelConfig,
    loaded_model: Option<String>,
    started_at: std::time::Instant,
    last_check_ts: Option<String>,
}

impl Default for KernelEngine {
    fn default() -> Self {
        Self::new(KernelConfig::default())
    }
}

impl KernelEngine {
    pub fn new(config: KernelConfig) -> Self {
        Self {
            config,
            loaded_model: None,
            started_at: std::time::Instant::now(),
            last_check_ts: None,
        }
    }

    pub fn config(&self) -> &KernelConfig {
        &self.config
    }

    /// Current engine status snapshot.
    pub fn status(&self) -> KernelStatus {
        KernelStatus {
            models_loaded: self.loaded_model.is_some(),
            ram_gb: 0.0,
            uptime_secs: self.started_at.elapsed().as_secs(),
            active_node: self.config.active_node.clone(),
            last_check: self.last_check_ts.clone(),
        }
    }

    /// Classify a situation description into severity + action.
    /// Deterministic rule-based — no LLM needed.
    pub fn classify(&self, situation: &str) -> KernelAction {
        let lower = situation.to_lowercase();
        let (severity, action, reason) = if lower.contains("daemon") && lower.contains("down") {
            (
                KernelSeverity::Critical,
                "restart",
                "daemon health check failed",
            )
        } else if lower.contains("disk") && lower.contains("full") {
            (KernelSeverity::Critical, "alert", "disk space critical")
        } else if lower.contains("stall") || lower.contains("stuck") {
            (KernelSeverity::Warn, "throttle", "stalled agent detected")
        } else if lower.contains("rate") && lower.contains("limit") {
            (KernelSeverity::Warn, "throttle", "rate limit hit")
        } else {
            (KernelSeverity::Ok, "none", "no action needed")
        };
        KernelAction {
            severity,
            action: action.to_string(),
            reason: reason.to_string(),
        }
    }

    /// Determine inference level for a query based on complexity heuristics.
    pub fn route_inference(&self, query: &str) -> InferenceLevel {
        let word_count = query.split_whitespace().count();
        let has_code_markers = query.contains("```")
            || query.contains("fn ")
            || query.contains("def ")
            || query.contains("class ");
        if word_count > 100 || has_code_markers {
            InferenceLevel::Cloud
        } else {
            InferenceLevel::Local
        }
    }

    /// Record a health check timestamp.
    pub fn record_check(&mut self) {
        self.last_check_ts = Some(chrono::Utc::now().to_rfc3339());
    }

    /// Set the active model name.
    pub fn set_loaded_model(&mut self, model: Option<String>) {
        self.loaded_model = model;
    }
}
