//! convergio-voice — STT/TTS engine for Convergio.
//!
//! Standalone audio processing: speech recognition (Whisper), synthesis (TTS),
//! voice activity detection, wake word, and intent extraction.
//! Used by convergio-kernel for Jarvis voice interface.

pub mod audio_util;
pub mod ext;
pub mod intent;
pub mod routes;
pub mod tts;
mod tts_backends;
pub mod types;
pub mod wake_word;
pub mod whisper;

pub use ext::VoiceExtension;
pub use intent::{extract_intent, Intent, IntentType};
pub use tts::{TtsBackend, TtsEngine, TtsError};
pub use types::{AudioFrame, SpeechSegment, VoiceConfig, VoiceError, VoiceState};
pub use whisper::{Transcription, WhisperEngine};

#[cfg(test)]
mod tests;
