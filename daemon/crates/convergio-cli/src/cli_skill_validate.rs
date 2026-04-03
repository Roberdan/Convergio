// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Validation helpers for skill lint — extracted from cli_skill.rs to keep both under 250 lines.

/// Extract a scalar YAML value (single-level key: value, unquoted or quoted).
pub(crate) fn yaml_get(content: &str, key: &str) -> Option<String> {
    for line in content.lines() {
        if let Some(rest) = line.strip_prefix(&format!("{key}:")) {
            let val = rest.trim().trim_matches('"').trim_matches('\'').to_string();
            if !val.is_empty() {
                return Some(val);
            }
        }
    }
    None
}

/// Extract a YAML list field. Supports both inline `[a, b]` and block `- item` forms.
pub(crate) fn yaml_get_list(content: &str, key: &str) -> Option<Vec<String>> {
    let mut lines = content.lines().peekable();
    while let Some(line) = lines.next() {
        if let Some(rest) = line.strip_prefix(&format!("{key}:")) {
            let rest = rest.trim();
            // Inline form: key: [a, b, c]
            if rest.starts_with('[') && rest.ends_with(']') {
                let inner = &rest[1..rest.len() - 1];
                let items: Vec<String> = inner
                    .split(',')
                    .map(|s| s.trim().trim_matches('"').trim_matches('\'').to_string())
                    .filter(|s| !s.is_empty())
                    .collect();
                return Some(items);
            }
            // Block form: following lines starting with "  - "
            if rest.is_empty() {
                let mut items = Vec::new();
                while let Some(next) = lines.peek() {
                    if let Some(item) = next.strip_prefix("  - ") {
                        items.push(item.trim().trim_matches('"').trim_matches('\'').to_string());
                        lines.next();
                    } else if next.starts_with("  ") || next.trim().is_empty() {
                        lines.next(); // skip blank/indented continuation
                    } else {
                        break;
                    }
                }
                return if items.is_empty() { None } else { Some(items) };
            }
        }
    }
    None
}

/// Compare semver strings: returns true if `ver >= min`.
pub(crate) fn semver_ge(ver: &str, min: &str) -> bool {
    let parse = |s: &str| -> (u32, u32, u32) {
        let p: Vec<u32> = s
            .split('.')
            .filter_map(|p| match p.parse::<u32>() {
                Ok(v) => Some(v),
                Err(_) => None,
            })
            .collect();
        (
            p.first().copied().unwrap_or(0),
            p.get(1).copied().unwrap_or(0),
            p.get(2).copied().unwrap_or(0),
        )
    };
    parse(ver) >= parse(min)
}

/// Validate skill name format: ^[a-z][a-z0-9-]*$
pub(crate) fn name_format_valid(name: &str) -> bool {
    let mut chars = name.chars();
    match chars.next() {
        Some(c) if c.is_ascii_lowercase() => {}
        _ => return false,
    }
    chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
}

/// Validate semver format: ^[0-9]+\.[0-9]+\.[0-9]+$
pub(crate) fn version_format_valid(ver: &str) -> bool {
    let parts: Vec<&str> = ver.split('.').collect();
    parts.len() == 3
        && parts
            .iter()
            .all(|p| !p.is_empty() && p.chars().all(|c| c.is_ascii_digit()))
}

/// Validate agent name format: ^[a-z][a-z0-9-]*$
pub(crate) fn agent_name_valid(name: &str) -> bool {
    name_format_valid(name)
}

/// Strip a leading H1 line from Markdown body.
pub(crate) fn strip_h1(md: &str) -> String {
    let mut lines = md.lines();
    match lines.next() {
        Some(first) if first.starts_with("# ") => lines.collect::<Vec<_>>().join("\n"),
        Some(first) => {
            let rest: Vec<_> = lines.collect();
            if rest.is_empty() {
                first.to_string()
            } else {
                format!("{first}\n{}", rest.join("\n"))
            }
        }
        None => String::new(),
    }
}

/// Capitalise first character of a string.
pub(crate) fn capitalise(s: &str) -> String {
    let mut chars = s.chars();
    match chars.next() {
        None => String::new(),
        Some(c) => c.to_uppercase().collect::<String>() + chars.as_str(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn yaml_get_extracts_unquoted() {
        let content = "name: my-skill\nversion: 1.0.0\n";
        assert_eq!(yaml_get(content, "name"), Some("my-skill".into()));
        assert_eq!(yaml_get(content, "version"), Some("1.0.0".into()));
    }

    #[test]
    fn yaml_get_list_inline() {
        let content = "requires-plugins: [plugA, plugB]\nname: foo\n";
        let items = yaml_get_list(content, "requires-plugins").unwrap();
        assert_eq!(items, vec!["plugA", "plugB"]);
    }

    #[test]
    fn yaml_get_list_block() {
        let content = "requires-agents:\n  - agent-one\n  - agent-two\nname: foo\n";
        let items = yaml_get_list(content, "requires-agents").unwrap();
        assert_eq!(items, vec!["agent-one", "agent-two"]);
    }

    #[test]
    fn yaml_get_list_returns_none_when_absent() {
        let content = "name: foo\n";
        assert!(yaml_get_list(content, "requires-plugins").is_none());
    }

    #[test]
    fn agent_name_valid_cases() {
        assert!(agent_name_valid("my-agent"));
        assert!(agent_name_valid("agent123"));
        assert!(!agent_name_valid("MyAgent"));
        assert!(!agent_name_valid("-bad"));
        assert!(!agent_name_valid(""));
    }

    #[test]
    fn semver_ge_comparisons() {
        assert!(semver_ge("2.0.0", "2.0.0"));
        assert!(semver_ge("3.0.0", "2.0.0"));
        assert!(!semver_ge("1.9.9", "2.0.0"));
    }

    #[test]
    fn name_format_valid_cases() {
        assert!(name_format_valid("my-skill"));
        assert!(!name_format_valid("MySkill"));
        assert!(!name_format_valid(""));
    }

    #[test]
    fn strip_h1_removes_title() {
        assert!(!strip_h1("# title\nbody").contains("# title"));
    }

    #[test]
    fn capitalise_first_char() {
        assert_eq!(capitalise("planner"), "Planner");
        assert_eq!(capitalise(""), "");
    }
}
