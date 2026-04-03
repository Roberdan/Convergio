// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Lint validators for skill directories — extracted from cli_skill.rs (Plan F, T4-01).

use crate::cli_skill::{LintResult, MIN_CONSTITUTION_VERSION, TOKEN_BUDGET_BYTES};
use crate::cli_skill_validate::{
    name_format_valid, semver_ge, version_format_valid, yaml_get, yaml_get_list,
};
use std::path::Path;

const REQUIRED_FIELDS: &[&str] = &[
    "name",
    "version",
    "description",
    "domain",
    "constitution-version",
    "license",
    "copyright",
];

pub(crate) fn lint_one(skill_dir: &Path) -> LintResult {
    let name = skill_dir
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();
    let yaml_path = skill_dir.join("skill.yaml");
    let md_path = skill_dir.join("SKILL.md");
    let mut msgs: Vec<String> = Vec::new();
    let mut failed = false;

    if yaml_path.is_file() {
        msgs.push(format!("[PASS] {name}: skill.yaml exists"));
    } else {
        msgs.push(format!("[FAIL] {name}: skill.yaml missing"));
        failed = true;
    }

    if yaml_path.is_file() {
        let yaml_content = std::fs::read_to_string(&yaml_path).unwrap_or_default();
        lint_yaml_fields(&name, &yaml_content, &mut msgs, &mut failed);
        lint_requires_plugins(&name, &yaml_content, &mut msgs, &mut failed);
        lint_requires_agents(&name, &yaml_content, &mut msgs, &mut failed);
    }

    if md_path.is_file() {
        msgs.push(format!("[PASS] {name}: SKILL.md exists"));
        let byte_size = std::fs::metadata(&md_path).map(|m| m.len()).unwrap_or(0);
        if byte_size <= TOKEN_BUDGET_BYTES {
            msgs.push(format!(
                "[PASS] {name}: token budget ({byte_size}/{TOKEN_BUDGET_BYTES} bytes)"
            ));
        } else {
            msgs.push(format!("[FAIL] {name}: SKILL.md over token budget ({byte_size}/{TOKEN_BUDGET_BYTES} bytes)"));
            failed = true;
        }
    } else {
        msgs.push(format!("[FAIL] {name}: SKILL.md missing"));
        failed = true;
    }

    LintResult {
        skill: name,
        ok: !failed,
        messages: msgs,
    }
}

fn lint_yaml_fields(name: &str, yaml: &str, msgs: &mut Vec<String>, failed: &mut bool) {
    let missing: Vec<&str> = REQUIRED_FIELDS
        .iter()
        .filter(|&&f| yaml_get(yaml, f).is_none())
        .copied()
        .collect();
    if missing.is_empty() {
        msgs.push(format!("[PASS] {name}: required fields present"));
    } else {
        msgs.push(format!(
            "[FAIL] {name}: required fields missing: {}",
            missing.join(", ")
        ));
        *failed = true;
    }
    match yaml_get(yaml, "constitution-version") {
        None => {
            msgs.push(format!("[FAIL] {name}: constitution-version not set"));
            *failed = true;
        }
        Some(ver) => {
            if semver_ge(&ver, MIN_CONSTITUTION_VERSION) {
                msgs.push(format!(
                    "[PASS] {name}: constitution version {ver} >= {MIN_CONSTITUTION_VERSION}"
                ));
            } else {
                msgs.push(format!(
                    "[FAIL] {name}: constitution version {ver} < {MIN_CONSTITUTION_VERSION}"
                ));
                *failed = true;
            }
        }
    }
    match yaml_get(yaml, "copyright") {
        Some(_) => msgs.push(format!("[PASS] {name}: copyright present")),
        None => {
            msgs.push(format!("[FAIL] {name}: copyright field missing or empty"));
            *failed = true;
        }
    }
    match yaml_get(yaml, "name") {
        Some(n) if name_format_valid(&n) => {
            msgs.push(format!("[PASS] {name}: name format valid ({n})"))
        }
        Some(n) => {
            msgs.push(format!(
                "[FAIL] {name}: name format invalid ({n}), must match ^[a-z][a-z0-9-]*$"
            ));
            *failed = true;
        }
        None => {
            msgs.push(format!("[FAIL] {name}: name field missing"));
            *failed = true;
        }
    }
    match yaml_get(yaml, "version") {
        Some(v) if version_format_valid(&v) => {
            msgs.push(format!("[PASS] {name}: version format valid ({v})"))
        }
        Some(v) => {
            msgs.push(format!(
                "[FAIL] {name}: version format invalid ({v}), must be semver"
            ));
            *failed = true;
        }
        None => {
            msgs.push(format!("[FAIL] {name}: version field missing"));
            *failed = true;
        }
    }
}

/// Validate requires-plugins: if present, must be non-empty list of strings.
fn lint_requires_plugins(name: &str, yaml: &str, msgs: &mut Vec<String>, failed: &mut bool) {
    if let Some(plugins) = yaml_get_list(yaml, "requires-plugins") {
        if plugins.is_empty() {
            msgs.push(format!(
                "[FAIL] {name}: requires-plugins is empty (remove field or add entries)"
            ));
            *failed = true;
        } else {
            msgs.push(format!(
                "[PASS] {name}: requires-plugins valid ({} entries)",
                plugins.len()
            ));
        }
    }
}

/// Validate requires-agents: each must match ^[a-z][a-z0-9-]*$.
fn lint_requires_agents(name: &str, yaml: &str, msgs: &mut Vec<String>, failed: &mut bool) {
    if let Some(agents) = yaml_get_list(yaml, "requires-agents") {
        if agents.is_empty() {
            msgs.push(format!(
                "[FAIL] {name}: requires-agents is empty (remove field or add entries)"
            ));
            *failed = true;
        } else {
            let invalid: Vec<&String> = agents.iter().filter(|a| !name_format_valid(a)).collect();
            if invalid.is_empty() {
                msgs.push(format!(
                    "[PASS] {name}: requires-agents valid ({} entries)",
                    agents.len()
                ));
            } else {
                let bad = invalid
                    .iter()
                    .map(|s| s.as_str())
                    .collect::<Vec<_>>()
                    .join(", ");
                msgs.push(format!("[FAIL] {name}: requires-agents invalid names: {bad} (must match ^[a-z][a-z0-9-]*$)"));
                *failed = true;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_lint_requires_plugins_valid() {
        let t = TempDir::new().unwrap();
        let sd = t.path().join("s");
        fs::create_dir(&sd).unwrap();
        fs::write(sd.join("skill.yaml"), "name: s\nversion: 1.0.0\ndescription: x\ndomain: y\nconstitution-version: 2.0.0\nlicense: MPL-2.0\ncopyright: x\nrequires-plugins: [mcp-github]\n").unwrap();
        fs::write(sd.join("SKILL.md"), "# s\n\nx.\n").unwrap();
        let r = lint_one(&sd);
        assert!(r.ok, "{:?}", r.messages);
        assert!(r
            .messages
            .iter()
            .any(|m| m.contains("requires-plugins valid")));
    }

    #[test]
    fn test_lint_requires_agents_invalid() {
        let t = TempDir::new().unwrap();
        let sd = t.path().join("s");
        fs::create_dir(&sd).unwrap();
        fs::write(sd.join("skill.yaml"), "name: s\nversion: 1.0.0\ndescription: x\ndomain: y\nconstitution-version: 2.0.0\nlicense: MPL-2.0\ncopyright: x\nrequires-agents:\n  - Agent_1\n").unwrap();
        fs::write(sd.join("SKILL.md"), "# s\n\nx.\n").unwrap();
        let r = lint_one(&sd);
        assert!(!r.ok);
        assert!(r
            .messages
            .iter()
            .any(|m| m.contains("requires-agents invalid")));
    }
}
