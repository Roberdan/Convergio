// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Multi-provider agent transpiler: one agent record in DB -> N provider format files.
// Distinct from cli_skill_transpile which operates on skill.yaml + SKILL.md directories.

/// Generate Claude Code .agent.md format with YAML frontmatter.
pub fn transpile_claude_code(name: &str, description: &str, model: &str, tools: &str) -> String {
    let mut out = String::new();
    out.push_str("---\n");
    out.push_str(&format!("name: {name}\n"));
    out.push_str(&format!("description: \"{description}\"\n"));
    out.push_str(&format!("model: {model}\n"));
    out.push_str("tools:\n");
    for tool in tools.split(',') {
        let tool = tool.trim();
        if !tool.is_empty() {
            out.push_str(&format!("  - {tool}\n"));
        }
    }
    out.push_str("---\n\n");
    out.push_str(&format!("# {name}\n\n"));
    out.push_str(description);
    out.push('\n');
    out
}

/// Generate GitHub Copilot CLI format (no YAML frontmatter).
pub fn transpile_copilot_cli(name: &str, description: &str, model: &str, tools: &str) -> String {
    let mut out = String::new();
    out.push_str(&format!("# {name}\n\n"));
    out.push_str(&format!("**Model**: {model}\n"));
    out.push_str(&format!("**Tools**: {tools}\n\n"));
    out.push_str(description);
    out.push('\n');
    out
}

/// Generate plain system prompt for generic LLM providers.
pub fn transpile_generic_llm(name: &str, description: &str, model: &str) -> String {
    let mut out = String::new();
    out.push_str(&format!("You are {name}. {description}\n\n"));
    out.push_str(&format!("Model: {model}\n"));
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_claude_code_has_yaml_frontmatter() {
        let result = transpile_claude_code(
            "code-reviewer",
            "Reviews pull requests for quality",
            "claude-sonnet-4-6",
            "view,edit,bash",
        );
        assert!(
            result.starts_with("---\n"),
            "must start with YAML frontmatter delimiter"
        );
        // Frontmatter must close before body
        let second_delimiter = result[4..].find("---\n");
        assert!(
            second_delimiter.is_some(),
            "must have closing frontmatter delimiter"
        );
        assert!(result.contains("name: code-reviewer"));
        assert!(result.contains("model: claude-sonnet-4-6"));
        assert!(result.contains("description: \"Reviews pull requests for quality\""));
    }

    #[test]
    fn test_claude_code_has_tools() {
        let result = transpile_claude_code(
            "debugger",
            "Debugging agent",
            "claude-opus-4-6",
            "view,edit,bash,grep",
        );
        assert!(result.contains("  - view\n"), "must list view tool");
        assert!(result.contains("  - edit\n"), "must list edit tool");
        assert!(result.contains("  - bash\n"), "must list bash tool");
        assert!(result.contains("  - grep\n"), "must list grep tool");
    }

    #[test]
    fn test_copilot_cli_no_frontmatter() {
        let result =
            transpile_copilot_cli("planner", "Creates execution plans", "gpt-4o", "view,bash");
        assert!(
            !result.starts_with("---"),
            "copilot CLI format must NOT have YAML frontmatter"
        );
        assert!(result.starts_with("# planner\n"));
        assert!(result.contains("**Model**: gpt-4o"));
        assert!(result.contains("**Tools**: view,bash"));
        assert!(result.contains("Creates execution plans"));
    }

    #[test]
    fn test_generic_llm_system_prompt() {
        let result = transpile_generic_llm(
            "architect",
            "Designs system architecture",
            "claude-opus-4-6",
        );
        assert!(result.starts_with("You are architect."));
        assert!(result.contains("Designs system architecture"));
        assert!(result.contains("Model: claude-opus-4-6"));
        // Must NOT have frontmatter or markdown headers
        assert!(!result.contains("---"));
        assert!(!result.contains("# "));
    }
}
