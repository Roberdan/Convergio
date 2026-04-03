//! TTS backend implementations — voxtral, qwen3, macOS say.

use super::tts::{TtsEngine, TtsError};

/// Resolve Python interpreter: CONVERGIO_PYTHON env or default "python3".
fn resolve_python() -> String {
    std::env::var("CONVERGIO_PYTHON").unwrap_or_else(|_| "python3".to_string())
}

impl TtsEngine {
    pub fn voxtral_available() -> bool {
        let python = resolve_python();
        std::process::Command::new(&python)
            .args([
                "-c",
                "from mlx_audio.tts.models.voxtral_tts import voxtral_tts; print('ok')",
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
    }

    pub fn qwen3_tts_available() -> bool {
        let python = resolve_python();
        std::process::Command::new(&python)
            .args([
                "-c",
                "from mlx_audio.tts.generate import generate_audio; print('ok')",
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map(|s| s.success())
            .unwrap_or(false)
    }

    pub fn say_available() -> bool {
        std::process::Command::new("say")
            .arg("--help")
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map(|_| true)
            .unwrap_or(false)
    }

    pub(crate) fn speak_via_say(&self, text: &str, locale: &str) -> Result<Vec<u8>, TtsError> {
        let voice = if locale.starts_with("it") {
            "Alice"
        } else {
            "Samantha"
        };
        let wav_path = self.temp_wav_path();
        let status = std::process::Command::new("say")
            .args([
                "-v",
                voice,
                "-o",
                wav_path.to_str().unwrap_or("/tmp/convergio_tts.wav"),
                "--data-format=LEI16@22050",
                text,
            ])
            .status()
            .map_err(|e| TtsError::SubprocessFailed(e.to_string()))?;
        if !status.success() {
            return Err(TtsError::SubprocessFailed(format!(
                "say exited with code {:?}",
                status.code()
            )));
        }
        std::fs::read(&wav_path).map_err(|e| TtsError::SubprocessFailed(format!("read wav: {e}")))
    }

    pub(crate) fn speak_via_qwen3(&self, text: &str, locale: &str) -> Result<Vec<u8>, TtsError> {
        let wav_dir = self.temp_wav_path();
        let lang = if locale.starts_with("it") { "it" } else { "en" };
        let python = resolve_python();
        let status = std::process::Command::new(&python)
            .args([
                "-m",
                "mlx_audio.tts.generate",
                "--model",
                "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16",
                "--text",
                text,
                "--voice",
                "Vivian",
                "--lang_code",
                lang,
                "--output_path",
                wav_dir.to_str().unwrap_or("/tmp/convergio_tts"),
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map_err(|e| TtsError::SubprocessFailed(e.to_string()))?;
        if !status.success() {
            return Err(TtsError::SubprocessFailed(
                "qwen3-tts exited with error".into(),
            ));
        }
        let audio_path = wav_dir.join("audio_000.wav");
        std::fs::read(&audio_path).map_err(|e| TtsError::SubprocessFailed(format!("read wav: {e}")))
    }

    pub(crate) fn speak_via_voxtral(&self, text: &str, locale: &str) -> Result<Vec<u8>, TtsError> {
        let wav_dir = self.temp_wav_path();
        let _ = locale;
        let voice = "casual_female";
        let python = resolve_python();
        let status = std::process::Command::new(&python)
            .args([
                "-m",
                "mlx_audio.tts.generate",
                "--model",
                "mlx-community/Voxtral-4B-TTS-2603-mlx-4bit",
                "--text",
                text,
                "--voice",
                voice,
                "--output_path",
                wav_dir.to_str().unwrap_or("/tmp/convergio_tts"),
            ])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .status()
            .map_err(|e| TtsError::SubprocessFailed(e.to_string()))?;
        if !status.success() {
            return Err(TtsError::SubprocessFailed(
                "voxtral-tts exited with error".into(),
            ));
        }
        let audio_path = wav_dir.join("audio_000.wav");
        std::fs::read(&audio_path).map_err(|e| TtsError::SubprocessFailed(format!("read wav: {e}")))
    }
}
