// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_skill and cli_skill_transpile modules.

use super::*;
use std::fs;
use tempfile::TempDir;

fn make_valid_skill(dir: &std::path::Path) {
    fs::write(
        dir.join("skill.yaml"),
        "\
name: my-skill\n\
version: 1.0.0\n\
description: A test skill\n\
domain: testing\n\
constitution-version: 2.0.0\n\
license: MPL-2.0\n\
copyright: Roberto D'Angelo, 2026\n",
    )
    .unwrap();
    fs::write(dir.join("SKILL.md"), "# my-skill\n\nDoes things.\n").unwrap();
}

#[test]
fn lint_valid_skill_passes() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_valid_skill(&skill_dir);
    let result = lint_one(&skill_dir);
    assert!(
        result.ok,
        "expected lint to pass; messages: {:?}",
        result.messages
    );
}

#[test]
fn lint_missing_yaml_fails() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("bad-skill");
    fs::create_dir(&skill_dir).unwrap();
    fs::write(skill_dir.join("SKILL.md"), "# bad-skill\n\nContent.\n").unwrap();
    let result = lint_one(&skill_dir);
    assert!(!result.ok);
    assert!(result
        .messages
        .iter()
        .any(|m| m.contains("[FAIL]") && m.contains("skill.yaml missing")));
}

#[test]
fn lint_missing_skill_md_fails() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("no-md");
    fs::create_dir(&skill_dir).unwrap();
    fs::write(
        skill_dir.join("skill.yaml"),
        "\
name: no-md\n\
version: 1.0.0\n\
description: A skill\n\
domain: testing\n\
constitution-version: 2.0.0\n\
license: MPL-2.0\n\
copyright: Roberto D'Angelo, 2026\n",
    )
    .unwrap();
    let result = lint_one(&skill_dir);
    assert!(!result.ok);
    assert!(result
        .messages
        .iter()
        .any(|m| m.contains("[FAIL]") && m.contains("SKILL.md missing")));
}

#[test]
fn lint_old_constitution_version_fails() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("old-skill");
    fs::create_dir(&skill_dir).unwrap();
    fs::write(
        skill_dir.join("skill.yaml"),
        "\
name: old-skill\n\
version: 1.0.0\n\
description: A skill\n\
domain: testing\n\
constitution-version: 1.0.0\n\
license: MPL-2.0\n\
copyright: Roberto D'Angelo, 2026\n",
    )
    .unwrap();
    fs::write(skill_dir.join("SKILL.md"), "# old-skill\n\nContent.\n").unwrap();
    let result = lint_one(&skill_dir);
    assert!(!result.ok);
    assert!(result
        .messages
        .iter()
        .any(|m| m.contains("[FAIL]") && m.contains("constitution version")));
}

#[test]
fn lint_over_token_budget_fails() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("big-skill");
    fs::create_dir(&skill_dir).unwrap();
    fs::write(
        skill_dir.join("skill.yaml"),
        "\
name: big-skill\n\
version: 1.0.0\n\
description: A skill\n\
domain: testing\n\
constitution-version: 2.0.0\n\
license: MPL-2.0\n\
copyright: Roberto D'Angelo, 2026\n",
    )
    .unwrap();
    fs::write(skill_dir.join("SKILL.md"), &"x".repeat(7000)).unwrap();
    let result = lint_one(&skill_dir);
    assert!(!result.ok);
    assert!(result
        .messages
        .iter()
        .any(|m| m.contains("[FAIL]") && m.contains("token budget")));
}

#[test]
fn lint_invalid_name_format_fails() {
    let tmp = TempDir::new().unwrap();
    let skill_dir = tmp.path().join("BadName");
    fs::create_dir(&skill_dir).unwrap();
    fs::write(
        skill_dir.join("skill.yaml"),
        "\
name: BadName\n\
version: 1.0.0\n\
description: A skill\n\
domain: testing\n\
constitution-version: 2.0.0\n\
license: MPL-2.0\n\
copyright: Roberto D'Angelo, 2026\n",
    )
    .unwrap();
    fs::write(skill_dir.join("SKILL.md"), "# BadName\n\nContent.\n").unwrap();
    let result = lint_one(&skill_dir);
    assert!(!result.ok);
    assert!(result
        .messages
        .iter()
        .any(|m| m.contains("[FAIL]") && m.contains("name format invalid")));
}

// Helper tests (yaml_get, semver_ge, name_format_valid, etc.) live in cli_skill_validate::tests

fn make_skill_with_yaml(dir: &std::path::Path, extra_yaml: &str) {
    fs::write(
        dir.join("skill.yaml"),
        format!(
            "\
name: test-skill\nversion: 1.0.0\ndescription: A skill\ndomain: testing\n\
constitution-version: 2.0.0\nlicense: MPL-2.0\ncopyright: Roberto D'Angelo, 2026\n{extra_yaml}"
        ),
    )
    .unwrap();
    fs::write(dir.join("SKILL.md"), "# test-skill\n\nContent.\n").unwrap();
}

#[test]
fn lint_no_requires_fields_still_passes() {
    let tmp = TempDir::new().unwrap();
    let sd = tmp.path().join("no-req-skill");
    fs::create_dir(&sd).unwrap();
    make_skill_with_yaml(&sd, "");
    let result = lint_one(&sd);
    assert!(result.ok, "messages: {:?}", result.messages);
}

#[test]
fn lint_requires_plugins_empty_fails() {
    let tmp = TempDir::new().unwrap();
    let sd = tmp.path().join("empty-plug");
    fs::create_dir(&sd).unwrap();
    make_skill_with_yaml(&sd, "requires-plugins: []\n");
    let r = lint_one(&sd);
    assert!(!r.ok);
    assert!(r
        .messages
        .iter()
        .any(|m| m.contains("requires-plugins is empty")));
}

#[test]
fn lint_requires_agents_empty_fails() {
    let tmp = TempDir::new().unwrap();
    let sd = tmp.path().join("empty-agent");
    fs::create_dir(&sd).unwrap();
    make_skill_with_yaml(&sd, "requires-agents: []\n");
    let r = lint_one(&sd);
    assert!(!r.ok);
    assert!(r
        .messages
        .iter()
        .any(|m| m.contains("requires-agents is empty")));
}

#[test]
fn skill_commands_enable_variant_exists() {
    let cmd = SkillCommands::Enable {
        skill_dir: PathBuf::from("/tmp/skill"),
        api_url: "http://localhost:8420".into(),
        human: false,
    };
    assert!(matches!(cmd, SkillCommands::Enable { .. }));
}

#[path = "cli_skill_tests_transpile.rs"]
mod transpile;
