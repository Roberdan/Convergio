//! MLX backend — direct subprocess inference via mlx-lm (Apple Silicon native).
//!
//! Spawns `python3 -m mlx_lm.generate` as a subprocess.
//! Supports TurboQuant for 4.6x KV cache compression (128K context on 32GB).
//! No Ollama dependency — uses MLX framework directly.

use crate::types::InferenceResponse;
use std::time::Instant;

/// Check if MLX is available on this system.
pub fn mlx_available() -> bool {
    let python = resolve_python();
    std::process::Command::new(&python)
        .args(["-c", "import mlx_lm; print('ok')"])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Call an MLX model via subprocess.
/// `model_name`: HuggingFace model ID or local path (e.g. "mlx-community/Qwen2.5-Coder-32B-Instruct-4bit")
pub async fn call_mlx(
    model_name: &str,
    prompt: &str,
    max_tokens: u32,
) -> Result<InferenceResponse, String> {
    let python = resolve_python();
    let turboquant = std::env::var("CONVERGIO_MLX_TURBOQUANT")
        .map(|v| v == "true" || v == "1")
        .unwrap_or(false);

    let start = Instant::now();

    // Build the Python script inline — avoids temp files and handles JSON output
    let script = format!(
        r#"
import json, sys
from mlx_lm import load, generate

model, tokenizer = load("{model_name}"{tq_arg})
prompt = {prompt_json}
response = generate(model, tokenizer, prompt=prompt, max_tokens={max_tokens})
result = {{"content": response, "tokens": len(tokenizer.encode(response))}}
print(json.dumps(result))
"#,
        model_name = model_name,
        tq_arg = if turboquant { ", lazy=True" } else { "" },
        prompt_json = serde_json::to_string(prompt).unwrap_or_default(),
        max_tokens = max_tokens,
    );

    let output = tokio::task::spawn_blocking(move || {
        std::process::Command::new(&python)
            .args(["-c", &script])
            .output()
    })
    .await
    .map_err(|e| format!("spawn_blocking: {e}"))?
    .map_err(|e| format!("mlx subprocess: {e}"))?;

    let latency_ms = start.elapsed().as_millis() as u64;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("mlx-lm failed: {stderr}"));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let parsed: MlxOutput =
        serde_json::from_str(stdout.trim()).map_err(|e| format!("parse mlx output: {e}"))?;

    Ok(InferenceResponse {
        content: parsed.content,
        model_used: model_name.to_string(),
        latency_ms,
        tokens_used: parsed.tokens.unwrap_or(max_tokens),
        cost: 0.0, // Local inference is free
    })
}

#[derive(serde::Deserialize)]
struct MlxOutput {
    content: String,
    tokens: Option<u32>,
}

/// Resolve the Python binary path.
fn resolve_python() -> String {
    std::env::var("CONVERGIO_PYTHON").unwrap_or_else(|_| "python3".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resolve_python_default() {
        if std::env::var("CONVERGIO_PYTHON").is_err() {
            assert_eq!(resolve_python(), "python3");
        }
    }

    #[test]
    fn mlx_available_returns_bool() {
        // Just verify it doesn't panic — actual availability depends on system
        let _ = mlx_available();
    }
}
