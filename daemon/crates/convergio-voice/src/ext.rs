//! Extension trait implementation for convergio-voice.

use convergio_types::extension::{Extension, Health, Metric};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

use super::tts::TtsEngine;

/// Voice extension — provides STT/TTS capabilities to the system.
pub struct VoiceExtension;

impl Extension for VoiceExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-voice".to_string(),
            description: "STT/TTS engine — speech recognition and synthesis".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Extension,
            provides: vec![
                Capability {
                    name: "tts".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Text-to-speech synthesis with multi-backend fallback".to_string(),
                },
                Capability {
                    name: "stt".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Speech-to-text via Whisper (local or API)".to_string(),
                },
                Capability {
                    name: "voice-pipeline".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Full voice pipeline: mic → VAD → wake → ASR → intent".to_string(),
                },
            ],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn health(&self) -> Health {
        if TtsEngine::say_available()
            || TtsEngine::qwen3_tts_available()
            || TtsEngine::voxtral_available()
        {
            Health::Ok
        } else {
            Health::Degraded {
                reason: "no TTS backend available".to_string(),
            }
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        vec![Metric {
            name: "voice_tts_backends_available".to_string(),
            value: [
                TtsEngine::say_available(),
                TtsEngine::qwen3_tts_available(),
                TtsEngine::voxtral_available(),
            ]
            .iter()
            .filter(|&&b| b)
            .count() as f64,
            labels: vec![],
        }]
    }
}
