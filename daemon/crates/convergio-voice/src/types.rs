//! Core voice types — state machine, configuration, errors, audio primitives.

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Voice pipeline state machine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum VoiceState {
    Idle,
    Listening,
    WakeDetected,
    Processing,
    Speaking,
}

impl std::fmt::Display for VoiceState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Idle => write!(f, "idle"),
            Self::Listening => write!(f, "listening"),
            Self::WakeDetected => write!(f, "wake_detected"),
            Self::Processing => write!(f, "processing"),
            Self::Speaking => write!(f, "speaking"),
        }
    }
}

/// Voice pipeline configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceConfig {
    /// VAD sensitivity threshold (0.0-1.0). Higher = more sensitive.
    pub vad_threshold: f32,
    /// Wake word to listen for. Default: "convergio".
    pub wake_word: String,
    /// Whisper model size. "small" or "medium".
    pub whisper_model: String,
    /// TTS voice name.
    pub tts_voice: String,
    /// TTS speech rate (0.5-2.0).
    pub tts_rate: f32,
    /// Whether to use local inference (MLX) or API fallback.
    pub prefer_local: bool,
}

impl Default for VoiceConfig {
    fn default() -> Self {
        Self {
            vad_threshold: 0.5,
            wake_word: "convergio".to_string(),
            whisper_model: "small".to_string(),
            tts_voice: "default".to_string(),
            tts_rate: 1.0,
            prefer_local: true,
        }
    }
}

#[derive(Debug, Error)]
pub enum VoiceError {
    #[error("audio error: {0}")]
    AudioError(String),
    #[error("VAD error: {0}")]
    VadError(String),
    #[error("ASR error: {0}")]
    AsrError(String),
    #[error("TTS error: {0}")]
    TtsError(String),
    #[error("intent error: {0}")]
    IntentError(String),
    #[error("pipeline error: {0}")]
    PipelineError(String),
    #[error("model not available: {0}")]
    ModelNotAvailable(String),
}

/// Audio frame for processing.
#[derive(Debug, Clone)]
pub struct AudioFrame {
    /// PCM samples at 16kHz, 16-bit.
    pub samples: Vec<i16>,
    /// Sample rate (always 16000).
    pub sample_rate: u32,
    /// Timestamp in milliseconds from stream start.
    pub timestamp_ms: u64,
}

/// Speech segment detected by VAD.
#[derive(Debug, Clone)]
pub struct SpeechSegment {
    pub start_ms: u64,
    pub end_ms: u64,
    pub samples: Vec<i16>,
}
