//! ASR engine — Whisper STT with lazy model loading and API fallback.

use std::path::PathBuf;

use super::types::{SpeechSegment, VoiceError};

/// Transcription result from Whisper STT.
#[derive(Debug, Clone)]
pub struct Transcription {
    pub text: String,
    pub language: String,
    pub confidence: f32,
    pub is_partial: bool,
}

/// Convert i16 PCM samples to f32 normalized [-1.0, 1.0].
pub fn samples_to_f32(samples: &[i16]) -> Vec<f32> {
    samples
        .iter()
        .map(|&s| s as f32 / i16::MAX as f32)
        .collect()
}

/// Resolve the GGML model path for whisper-rs.
/// Searches: $WHISPER_MODEL_PATH, ~/.cache/whisper/, bundled data/.
fn resolve_model_path(model_size: &str) -> PathBuf {
    let filename = format!("ggml-{model_size}.bin");

    if let Ok(p) = std::env::var("WHISPER_MODEL_PATH") {
        let path = PathBuf::from(p);
        if path.exists() {
            return path;
        }
    }

    if let Some(home) = dirs::home_dir() {
        let cache_path = home.join(".cache/whisper").join(&filename);
        if cache_path.exists() {
            return cache_path;
        }
    }

    let local_path = PathBuf::from("data/models").join(&filename);
    if local_path.exists() {
        return local_path;
    }

    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".cache/whisper")
        .join(filename)
}

/// ASR engine wrapping whisper-rs for native Rust STT.
/// Loads GGML model on first transcription (lazy init).
pub struct WhisperEngine {
    model_size: String,
    prefer_local: bool,
}

impl WhisperEngine {
    pub fn new(model_size: &str, prefer_local: bool) -> Self {
        Self {
            model_size: model_size.to_string(),
            prefer_local,
        }
    }

    pub fn model_size(&self) -> &str {
        &self.model_size
    }

    pub fn prefers_local(&self) -> bool {
        self.prefer_local
    }

    /// Return the resolved model file path for this engine's model size.
    pub fn model_path(&self) -> String {
        resolve_model_path(&self.model_size)
            .to_string_lossy()
            .into_owned()
    }

    /// Transcribe a speech segment.
    /// Currently returns a stub — full whisper-rs integration requires the
    /// `voice` feature flag with native audio dependencies.
    pub fn transcribe(&self, segment: &SpeechSegment) -> Result<Transcription, VoiceError> {
        if segment.samples.is_empty() {
            return Err(VoiceError::AsrError("empty audio segment".to_string()));
        }

        if self.prefer_local {
            self.transcribe_local(segment)
        } else {
            self.transcribe_api(segment)
        }
    }

    fn transcribe_local(&self, _segment: &SpeechSegment) -> Result<Transcription, VoiceError> {
        Err(VoiceError::ModelNotAvailable(
            "whisper-rs native inference requires voice feature flag".to_string(),
        ))
    }

    fn transcribe_api(&self, _segment: &SpeechSegment) -> Result<Transcription, VoiceError> {
        Err(VoiceError::AsrError(
            "whisper API fallback not yet implemented".to_string(),
        ))
    }
}
