//! Template rendering — substitutes `{{variable}}` placeholders with values.

use std::collections::HashMap;

use crate::types::PromptVariable;

/// Render a template body by substituting `{{var}}` placeholders.
///
/// Returns an error string if a required variable is missing and has no default.
pub fn render(
    body: &str,
    variables: &[PromptVariable],
    values: &HashMap<String, String>,
) -> Result<String, String> {
    let mut result = body.to_string();

    for var in variables {
        let placeholder = format!("{{{{{}}}}}", var.name);
        if let Some(value) = values.get(&var.name) {
            result = result.replace(&placeholder, value);
        } else if let Some(ref default) = var.default_value {
            result = result.replace(&placeholder, default);
        } else if var.required {
            return Err(format!("missing required variable: {}", var.name));
        }
        // Optional without default: leave placeholder removed.
        else {
            result = result.replace(&placeholder, "");
        }
    }
    Ok(result)
}

/// Count the approximate number of tokens in a string.
/// Uses a simple heuristic: ~4 chars per token for English text.
pub fn estimate_tokens(text: &str) -> u64 {
    let chars = text.len() as u64;
    // Rough approximation: 1 token ~ 4 characters.
    chars.div_ceil(4)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn var(name: &str, required: bool, default: Option<&str>) -> PromptVariable {
        PromptVariable {
            name: name.into(),
            description: String::new(),
            required,
            default_value: default.map(String::from),
        }
    }

    #[test]
    fn basic_substitution() {
        let body = "You are {{role}} at {{org}}.";
        let vars = vec![var("role", true, None), var("org", true, None)];
        let mut values = HashMap::new();
        values.insert("role".into(), "engineer".into());
        values.insert("org".into(), "Convergio".into());
        let result = render(body, &vars, &values).unwrap();
        assert_eq!(result, "You are engineer at Convergio.");
    }

    #[test]
    fn default_value_used() {
        let body = "Hello {{name}}, welcome to {{place}}.";
        let vars = vec![
            var("name", true, None),
            var("place", false, Some("the system")),
        ];
        let mut values = HashMap::new();
        values.insert("name".into(), "Elena".into());
        let result = render(body, &vars, &values).unwrap();
        assert_eq!(result, "Hello Elena, welcome to the system.");
    }

    #[test]
    fn missing_required_fails() {
        let body = "{{agent}} does {{task}}";
        let vars = vec![var("agent", true, None), var("task", true, None)];
        let values = HashMap::new();
        let err = render(body, &vars, &values).unwrap_err();
        assert!(err.contains("agent"));
    }

    #[test]
    fn optional_without_default_removed() {
        let body = "prefix{{opt}}suffix";
        let vars = vec![var("opt", false, None)];
        let values = HashMap::new();
        let result = render(body, &vars, &values).unwrap();
        assert_eq!(result, "prefixsuffix");
    }

    #[test]
    fn estimate_tokens_reasonable() {
        let text = "This is a test sentence with about ten tokens.";
        let tokens = estimate_tokens(text);
        // ~47 chars / 4 = ~12, should be in 10-15 range.
        assert!(tokens >= 8 && tokens <= 20, "got {tokens}");
    }
}
