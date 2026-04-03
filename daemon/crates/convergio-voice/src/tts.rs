//! TTS engine — Voxtral MLX primary, Qwen3 secondary, macOS `say` fallback.
//!
//! Uses phrase caching to avoid re-synthesis. Latency target: <2s for 20 words.

use std::collections::HashMap;
use std::path::PathBuf;
use std::time::Instant;

/// Error variants for TTS operations.
#[derive(Debug, thiserror::Error)]
pub enum TtsError {
    #[error("tts subprocess failed: {0}")]
    SubprocessFailed(String),
    #[error("tts backend unavailable: {0}")]
    Unavailable(String),
}

/// Supported TTS backend strategies (priority: Voxtral > Qwen3 > macOS Say).
#[derive(Debug, Clone, PartialEq)]
pub enum TtsBackend {
    VoxtralMlx,
    Qwen3Tts,
    MacOsSay,
}

impl TtsBackend {
    pub fn display_name(&self) -> &'static str {
        match self {
            Self::VoxtralMlx => "Voxtral Mini MLX",
            Self::Qwen3Tts => "Qwen3 TTS Vivian",
            Self::MacOsSay => "macOS Say",
        }
    }
}

/// TTS engine with phrase caching and multi-backend fallback.
pub struct TtsEngine {
    pub model_name: String,
    pub loaded: bool,
    phrase_cache: HashMap<String, Vec<u8>>,
    backend: TtsBackend,
    pub(crate) wav_path_override: Option<PathBuf>,
}

impl Default for TtsEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl TtsEngine {
    pub fn new() -> Self {
        let backend = if Self::voxtral_available() {
            TtsBackend::VoxtralMlx
        } else if Self::qwen3_tts_available() {
            TtsBackend::Qwen3Tts
        } else {
            TtsBackend::MacOsSay
        };
        let model_name = match &backend {
            TtsBackend::VoxtralMlx => "voxtral-mini-mlx".to_string(),
            TtsBackend::Qwen3Tts => "qwen3-tts-vivian".to_string(),
            TtsBackend::MacOsSay => "macos-say-alice".to_string(),
        };
        Self {
            model_name,
            loaded: true,
            phrase_cache: HashMap::new(),
            backend,
            wav_path_override: None,
        }
    }

    pub fn backend(&self) -> &TtsBackend {
        &self.backend
    }

    /// Synthesise `text` in the given `locale` and return WAV bytes.
    pub fn speak(&mut self, text: &str, locale: &str) -> Result<Vec<u8>, TtsError> {
        let cache_key = format!("{locale}:{text}");
        if let Some(cached) = self.phrase_cache.get(&cache_key) {
            tracing::debug!(text, locale, "tts cache hit");
            return Ok(cached.clone());
        }

        let start = Instant::now();
        let wav = match self.backend {
            TtsBackend::VoxtralMlx => self.speak_via_voxtral(text, locale)?,
            TtsBackend::Qwen3Tts => self.speak_via_qwen3(text, locale)?,
            TtsBackend::MacOsSay => self.speak_via_say(text, locale)?,
        };
        let elapsed = start.elapsed();
        tracing::info!(
            text, locale, elapsed_ms = elapsed.as_millis(),
            backend = ?self.backend, "tts synthesis complete"
        );
        if elapsed.as_secs() >= 2 {
            tracing::warn!(elapsed_ms = elapsed.as_millis(), "tts latency exceeded 2s");
        }

        self.phrase_cache.insert(cache_key, wav.clone());
        Ok(wav)
    }

    pub(crate) fn temp_wav_path(&self) -> PathBuf {
        if let Some(ref p) = self.wav_path_override {
            return p.clone();
        }
        PathBuf::from(format!("/tmp/convergio_tts_{}.wav", std::process::id()))
    }
}
