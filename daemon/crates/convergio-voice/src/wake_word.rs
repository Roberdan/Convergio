//! Wake word detector — text-based substring matching.
//!
//! When the `voice` feature is enabled, raw audio frames can be fed through
//! VAD + Whisper micro-transcription. Without it, only `check_text` is available.

use super::types::VoiceError;

/// Wake word detector using text-based matching.
pub struct WakeWordDetector {
    wake_word: String,
    detected: bool,
}

impl WakeWordDetector {
    pub fn new(wake_word: &str, _vad_threshold: f32, _whisper_model: &str) -> Self {
        Self {
            wake_word: wake_word.to_lowercase(),
            detected: false,
        }
    }

    /// Check transcribed text for the wake word (case-insensitive substring).
    pub fn check_text(&mut self, text: &str) -> Result<bool, VoiceError> {
        let normalised = text.to_lowercase();
        let found = normalised.contains(&self.wake_word);
        if found {
            self.detected = true;
        }
        Ok(found)
    }

    /// Reset detection state.
    pub fn reset(&mut self) {
        self.detected = false;
    }

    pub fn is_detected(&self) -> bool {
        self.detected
    }

    pub fn wake_word(&self) -> &str {
        &self.wake_word
    }
}
