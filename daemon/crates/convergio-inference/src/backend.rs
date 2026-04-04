//! HTTP backend — calls real model APIs (Ollama, OpenAI-compatible).
//!
//! Ollama exposes an OpenAI-compatible endpoint at /v1/chat/completions.
//! Cloud providers (Anthropic, OpenAI) also follow this format.

use std::time::Instant;

use serde::{Deserialize, Serialize};

use crate::types::{InferenceResponse, ModelEndpoint, ModelProvider};

#[derive(Serialize)]
struct ChatRequest<'a> {
    model: &'a str,
    messages: Vec<ChatMessage<'a>>,
    max_tokens: u32,
    stream: bool,
}

#[derive(Serialize)]
struct ChatMessage<'a> {
    role: &'a str,
    content: &'a str,
}

#[derive(Deserialize)]
struct ChatResponse {
    choices: Vec<Choice>,
    usage: Option<Usage>,
}

#[derive(Deserialize)]
struct Choice {
    message: ChoiceMessage,
}

#[derive(Deserialize)]
struct ChoiceMessage {
    content: String,
}

#[derive(Deserialize)]
struct Usage {
    #[serde(default)]
    total_tokens: u32,
}

/// Call a model endpoint and return the real response.
/// Falls back to echo mode if the endpoint is unreachable.
pub async fn call_model(
    endpoint: &ModelEndpoint,
    prompt: &str,
    max_tokens: u32,
) -> Result<InferenceResponse, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(120))
        .build()
        .map_err(|e| format!("http client: {e}"))?;

    // Ollama model name: strip provider prefix if present
    let model_name = endpoint.name.split('/').next_back().unwrap_or(&endpoint.name);

    let url = format!("{}/v1/chat/completions", endpoint.url.trim_end_matches('/'));

    let body = ChatRequest {
        model: model_name,
        messages: vec![ChatMessage {
            role: "user",
            content: prompt,
        }],
        max_tokens,
        stream: false,
    };

    let start = Instant::now();

    let mut req = client.post(&url).json(&body);

    // Cloud providers need auth headers (loaded from daemon env file)
    if endpoint.provider == ModelProvider::Cloud {
        if let Ok(key) = std::env::var("CONVERGIO_ANTHROPIC_TOKEN") {
            req = req
                .header("x-api-key", &key)
                .header("anthropic-version", "2023-06-01");
        } else if let Ok(key) = std::env::var("CONVERGIO_OPENAI_TOKEN") {
            req = req.header("Authorization", format!("Bearer {key}"));
        }
    }

    let resp = req.send().await.map_err(|e| format!("request: {e}"))?;
    let latency_ms = start.elapsed().as_millis() as u64;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("model returned {status}: {body}"));
    }

    let chat: ChatResponse = resp
        .json()
        .await
        .map_err(|e| format!("parse response: {e}"))?;

    let content = chat
        .choices
        .into_iter()
        .next()
        .map(|c| c.message.content)
        .unwrap_or_default();

    let tokens_used = chat.usage.map(|u| u.total_tokens).unwrap_or(max_tokens);

    let cost = (tokens_used as f64 / 1000.0) * endpoint.cost_per_1k_input;

    Ok(InferenceResponse {
        content,
        model_used: endpoint.name.clone(),
        latency_ms,
        tokens_used,
        cost,
    })
}

#[cfg(test)]
mod tests {
    #[allow(unused_imports)]
    use super::*;

    #[test]
    fn model_name_strips_prefix() {
        let name = "ollama/llama3.2";
        let stripped = name.split('/').last().unwrap_or(name);
        assert_eq!(stripped, "llama3.2");
    }

    #[test]
    fn model_name_no_prefix() {
        let name = "llama3.2";
        let stripped = name.split('/').last().unwrap_or(name);
        assert_eq!(stripped, "llama3.2");
    }
}
