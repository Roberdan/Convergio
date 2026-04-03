//! convergio-kernel — Jarvis: local LLM + health monitoring + evidence gate.
//!
//! Extension: pluggable, feature-gated. Provides local inference (Qwen via MLX),
//! health monitoring (30s cycle), evidence gate (Article VI), voice routing,
//! Telegram notifications, and deterministic recovery.
//!
//! DB tables: kernel_events, kernel_verifications, kernel_config, knowledge_base.

pub mod engine;
pub mod ext;
pub mod monitor;
pub mod recover;
pub mod types;
pub mod verify;

pub use ext::KernelExtension;
pub use types::{
    EvidenceCheck, EvidenceReport, InferenceLevel, KernelAction, KernelCheckResult, KernelConfig,
    KernelSeverity, KernelStatus, VoiceIntent,
};

#[cfg(test)]
mod tests;
