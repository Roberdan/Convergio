//! Load model endpoints from TOML config or hardcoded defaults.

use crate::types::{InferenceTier, ModelEndpoint, ModelProvider};
use serde::Deserialize;

#[derive(Deserialize)]
struct ModelsConfig {
    models: Vec<ModelEntry>,
}

#[derive(Deserialize)]
struct ModelEntry {
    name: String,
    provider: String,
    url: String,
    cost_per_1k_input: f64,
    cost_per_1k_output: f64,
    tier_min: String,
    tier_max: String,
}

/// Load model endpoints from a TOML config file.
/// Falls back to hardcoded defaults if the file is missing.
pub fn load_model_endpoints(config_path: Option<&str>) -> Vec<ModelEndpoint> {
    let entries = match config_path.and_then(|p| std::fs::read_to_string(p).ok()) {
        Some(contents) => parse_toml(&contents),
        None => hardcoded_defaults(),
    };
    entries.into_iter().map(|e| entry_to_endpoint(e)).collect()
}

/// Parse TOML string into model entries.
fn parse_toml(contents: &str) -> Vec<ModelEntry> {
    match toml::from_str::<ModelsConfig>(contents) {
        Ok(cfg) => cfg.models,
        Err(e) => {
            tracing::warn!(error = %e, "failed to parse models config, using defaults");
            hardcoded_defaults()
        }
    }
}

fn hardcoded_defaults() -> Vec<ModelEntry> {
    vec![
        ModelEntry {
            name: "llama3".into(),
            provider: "local".into(),
            url: "${CONVERGIO_OLLAMA_URL:-http://localhost:11434}/v1/chat/completions".into(),
            cost_per_1k_input: 0.0,
            cost_per_1k_output: 0.0,
            tier_min: "t1".into(),
            tier_max: "t3".into(),
        },
        ModelEntry {
            name: "claude-sonnet".into(),
            provider: "cloud".into(),
            url: "https://api.anthropic.com/v1/messages".into(),
            cost_per_1k_input: 3.0,
            cost_per_1k_output: 15.0,
            tier_min: "t2".into(),
            tier_max: "t3".into(),
        },
        ModelEntry {
            name: "claude-opus".into(),
            provider: "cloud".into(),
            url: "https://api.anthropic.com/v1/messages".into(),
            cost_per_1k_input: 15.0,
            cost_per_1k_output: 75.0,
            tier_min: "t3".into(),
            tier_max: "t4".into(),
        },
        ModelEntry {
            name: "gpt-4o".into(),
            provider: "cloud".into(),
            url: "https://api.openai.com/v1/chat/completions".into(),
            cost_per_1k_input: 2.5,
            cost_per_1k_output: 10.0,
            tier_min: "t2".into(),
            tier_max: "t4".into(),
        },
    ]
}

fn entry_to_endpoint(e: ModelEntry) -> ModelEndpoint {
    let url = resolve_env(&e.url);
    let provider = match e.provider.as_str() {
        "local" => ModelProvider::Local,
        _ => ModelProvider::Cloud,
    };
    let healthy = match provider {
        ModelProvider::Local => true,
        ModelProvider::Cloud => is_cloud_model_available(&url),
    };
    ModelEndpoint {
        name: e.name,
        provider,
        url,
        cost_per_1k_input: e.cost_per_1k_input,
        cost_per_1k_output: e.cost_per_1k_output,
        tier_range: (parse_tier(&e.tier_min), parse_tier(&e.tier_max)),
        healthy,
    }
}

/// Parse tier string ("t1"..."t4") to InferenceTier.
fn parse_tier(s: &str) -> InferenceTier {
    InferenceTier::from_label(s).unwrap_or(InferenceTier::T2Standard)
}

/// Resolve env var placeholders: `${VAR:-default}` and `${VAR}`.
fn resolve_env(s: &str) -> String {
    let mut result = s.to_string();
    while let Some(start) = result.find("${") {
        let end = match result[start..].find('}') {
            Some(e) => start + e,
            None => break,
        };
        let inner = &result[start + 2..end];
        let resolved = if let Some(sep) = inner.find(":-") {
            let var = &inner[..sep];
            let default = &inner[sep + 2..];
            std::env::var(var).unwrap_or_else(|_| default.to_string())
        } else {
            std::env::var(inner).unwrap_or_default()
        };
        result = format!("{}{}{}", &result[..start], resolved, &result[end + 1..]);
    }
    result
}

/// Check if a cloud model has its required API key env var set.
fn is_cloud_model_available(url: &str) -> bool {
    if url.contains("anthropic.com") {
        std::env::var("CONVERGIO_ANTHROPIC_TOKEN").is_ok()
    } else if url.contains("openai.com") {
        std::env::var("CONVERGIO_OPENAI_TOKEN").is_ok()
    } else {
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_env_with_default() {
        // Unset var should fall back to default
        std::env::remove_var("CONVERGIO_TEST_RESOLVE_99");
        let out = resolve_env("${CONVERGIO_TEST_RESOLVE_99:-http://fallback:1234}/api");
        assert_eq!(out, "http://fallback:1234/api");
    }

    #[test]
    fn test_resolve_env_with_set_var() {
        std::env::set_var("CONVERGIO_TEST_RESOLVE_SET", "http://custom:5678");
        let out = resolve_env("${CONVERGIO_TEST_RESOLVE_SET:-http://fallback}/api");
        assert_eq!(out, "http://custom:5678/api");
        std::env::remove_var("CONVERGIO_TEST_RESOLVE_SET");
    }

    #[test]
    fn test_parse_tier() {
        assert_eq!(parse_tier("t1"), InferenceTier::T1Trivial);
        assert_eq!(parse_tier("t2"), InferenceTier::T2Standard);
        assert_eq!(parse_tier("t3"), InferenceTier::T3Complex);
        assert_eq!(parse_tier("t4"), InferenceTier::T4Critical);
        assert_eq!(parse_tier("invalid"), InferenceTier::T2Standard);
    }

    #[test]
    fn test_load_defaults() {
        let endpoints = load_model_endpoints(None);
        assert_eq!(endpoints.len(), 4);
        let names: Vec<&str> = endpoints.iter().map(|e| e.name.as_str()).collect();
        assert!(names.contains(&"llama3"));
        assert!(names.contains(&"claude-sonnet"));
        assert!(names.contains(&"claude-opus"));
        assert!(names.contains(&"gpt-4o"));
    }

    #[test]
    fn test_load_from_toml() {
        let toml_str = r#"
[[models]]
name = "test-local"
provider = "local"
url = "http://localhost:9999/v1"
cost_per_1k_input = 0.0
cost_per_1k_output = 0.0
tier_min = "t1"
tier_max = "t2"
"#;
        let entries = parse_toml(toml_str);
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].name, "test-local");
        assert_eq!(entries[0].tier_min, "t1");
    }

    #[test]
    fn test_local_models_are_healthy() {
        let endpoints = load_model_endpoints(None);
        let llama = endpoints.iter().find(|e| e.name == "llama3").unwrap();
        assert!(llama.healthy);
        assert_eq!(llama.provider, ModelProvider::Local);
    }
}
