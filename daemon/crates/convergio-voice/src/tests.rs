//! Tests for convergio-voice.

use super::*;

mod types_tests {
    use super::*;

    #[test]
    fn voice_state_display() {
        assert_eq!(VoiceState::Idle.to_string(), "idle");
        assert_eq!(VoiceState::Listening.to_string(), "listening");
        assert_eq!(VoiceState::WakeDetected.to_string(), "wake_detected");
        assert_eq!(VoiceState::Processing.to_string(), "processing");
        assert_eq!(VoiceState::Speaking.to_string(), "speaking");
    }

    #[test]
    fn voice_config_default() {
        let cfg = VoiceConfig::default();
        assert_eq!(cfg.vad_threshold, 0.5);
        assert_eq!(cfg.wake_word, "convergio");
        assert_eq!(cfg.whisper_model, "small");
        assert!(cfg.prefer_local);
    }
}

mod audio_util_tests {
    use super::audio_util::*;

    #[test]
    fn stereo_to_mono_averages_pairs() {
        let stereo = vec![100, 200, -50, 50];
        let mono = stereo_to_mono(&stereo);
        assert_eq!(mono, vec![150, 0]);
    }

    #[test]
    fn stereo_to_mono_empty() {
        let mono = stereo_to_mono(&[]);
        assert!(mono.is_empty());
    }

    #[test]
    fn resample_identity() {
        let samples = vec![1, 2, 3, 4, 5];
        let out = resample(&samples, 16000, 16000);
        assert_eq!(out, samples);
    }

    #[test]
    fn resample_downsample() {
        let samples: Vec<i16> = (0..100).collect();
        let out = resample(&samples, 48000, 16000);
        assert!(out.len() < samples.len());
        assert_eq!(out.len(), 33);
    }

    #[test]
    fn resample_empty() {
        let out = resample(&[], 48000, 16000);
        assert!(out.is_empty());
    }
}

mod wake_word_tests {
    use super::wake_word::WakeWordDetector;

    #[test]
    fn detects_wake_word_case_insensitive() {
        let mut det = WakeWordDetector::new("convergio", 0.5, "small");
        assert!(!det.is_detected());
        let found = det.check_text("Hey Convergio, what's up?").unwrap();
        assert!(found);
        assert!(det.is_detected());
    }

    #[test]
    fn no_false_positive() {
        let mut det = WakeWordDetector::new("convergio", 0.5, "small");
        let found = det.check_text("hello world").unwrap();
        assert!(!found);
        assert!(!det.is_detected());
    }

    #[test]
    fn reset_clears_state() {
        let mut det = WakeWordDetector::new("jarvis", 0.5, "small");
        det.check_text("hey jarvis").unwrap();
        assert!(det.is_detected());
        det.reset();
        assert!(!det.is_detected());
    }
}

mod intent_tests {
    use super::intent::*;

    #[test]
    fn control_intent_start_voice() {
        let intent = extract_intent("start voice").unwrap();
        assert_eq!(intent.intent_type, IntentType::Control);
        assert_eq!(intent.command.as_deref(), Some("cvg voice start"));
        assert!(intent.confidence > 0.8);
    }

    #[test]
    fn command_intent_list_plans() {
        let intent = extract_intent("list all plans").unwrap();
        assert_eq!(intent.intent_type, IntentType::Command);
        assert_eq!(intent.command.as_deref(), Some("cvg plan list"));
    }

    #[test]
    fn query_intent() {
        let intent = extract_intent("what agents are running?").unwrap();
        assert_eq!(intent.intent_type, IntentType::Query);
    }

    #[test]
    fn navigation_intent() {
        let intent = extract_intent("switch to mesh view").unwrap();
        assert_eq!(intent.intent_type, IntentType::Navigation);
        assert_eq!(intent.command.as_deref(), Some("navigate:mesh"));
    }

    #[test]
    fn ambiguous_intent() {
        let intent = extract_intent("banana").unwrap();
        assert_eq!(intent.intent_type, IntentType::Ambiguous);
        assert!(intent.confidence < 0.5);
    }
}

mod whisper_tests {
    use super::types::SpeechSegment;
    use super::whisper::*;

    #[test]
    fn empty_segment_errors() {
        let engine = WhisperEngine::new("small", true);
        let segment = SpeechSegment {
            start_ms: 0,
            end_ms: 0,
            samples: vec![],
        };
        assert!(engine.transcribe(&segment).is_err());
    }

    #[test]
    fn model_path_resolves() {
        let engine = WhisperEngine::new("small", true);
        let path = engine.model_path();
        assert!(path.contains("ggml-small.bin"));
    }
}

mod tts_tests {
    use super::tts::*;

    #[test]
    fn tts_engine_creates_with_backend() {
        let engine = TtsEngine::new();
        assert!(engine.loaded);
        assert!(!engine.model_name.is_empty());
    }

    #[test]
    fn tts_backend_display_names() {
        assert_eq!(TtsBackend::VoxtralMlx.display_name(), "Voxtral Mini MLX");
        assert_eq!(TtsBackend::Qwen3Tts.display_name(), "Qwen3 TTS Vivian");
        assert_eq!(TtsBackend::MacOsSay.display_name(), "macOS Say");
    }
}

mod ext_tests {
    use super::ext::VoiceExtension;
    use convergio_types::extension::Extension;
    use convergio_types::manifest::ModuleKind;

    #[test]
    fn manifest_is_extension_kind() {
        let ext = VoiceExtension;
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-voice");
        assert!(matches!(m.kind, ModuleKind::Extension));
        assert!(!m.provides.is_empty());
    }

    #[test]
    fn health_check_runs() {
        let ext = VoiceExtension;
        let _health = ext.health();
    }

    #[test]
    fn metrics_reports_backends() {
        let ext = VoiceExtension;
        let metrics = ext.metrics();
        assert_eq!(metrics.len(), 1);
        assert_eq!(metrics[0].name, "voice_tts_backends_available");
    }
}
