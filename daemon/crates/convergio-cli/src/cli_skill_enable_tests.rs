// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Integration tests for cli_skill_enable plugin activation.

use super::activate_plugins;
use std::fs;
use tempfile::TempDir;

fn make_skill_yaml(dir: &std::path::Path, plugins: &[&str]) -> std::path::PathBuf {
    let plugin_list = if plugins.is_empty() {
        String::new()
    } else {
        format!("requires-plugins: [{}]\n", plugins.join(", "))
    };
    let yaml = format!(
        "name: test-skill\nversion: 1.0.0\ndescription: A skill\ndomain: testing\n\
         constitution-version: 2.0.0\nlicense: MPL-2.0\ncopyright: Roberto D'Angelo, 2026\n{plugin_list}"
    );
    let path = dir.join("skill.yaml");
    fs::write(&path, yaml).unwrap();
    path
}

fn make_settings_json(claude_dir: &std::path::Path, content: &str) {
    fs::create_dir_all(claude_dir).unwrap();
    fs::write(claude_dir.join("settings.json"), content).unwrap();
}

fn read_allowed_plugins(claude_dir: &std::path::Path) -> Vec<String> {
    let path = claude_dir.join("settings.json");
    let text = fs::read_to_string(&path).unwrap();
    let val: serde_json::Value = serde_json::from_str(&text).unwrap();
    val["allowedPlugins"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect()
}

#[test]
fn test_enable_activates_plugins_creates_settings_when_absent() {
    let tmp = TempDir::new().unwrap();
    let claude_dir = tmp.path().join(".claude");
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_skill_yaml(&skill_dir, &["mcp-github", "mcp-slack"]);

    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let result = activate_plugins(&yaml, &claude_dir).unwrap();

    assert_eq!(result.added, vec!["mcp-github", "mcp-slack"]);
    assert!(result.skipped.is_empty());
    let plugins = read_allowed_plugins(&claude_dir);
    assert!(plugins.contains(&"mcp-github".to_string()));
    assert!(plugins.contains(&"mcp-slack".to_string()));
}

#[test]
fn test_enable_activates_plugins_merges_with_existing() {
    let tmp = TempDir::new().unwrap();
    let claude_dir = tmp.path().join(".claude");
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_skill_yaml(&skill_dir, &["mcp-github", "mcp-new"]);
    make_settings_json(
        &claude_dir,
        r#"{"allowedPlugins":["mcp-github","mcp-existing"]}"#,
    );

    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let result = activate_plugins(&yaml, &claude_dir).unwrap();

    // mcp-github already present → skipped; mcp-new → added
    assert_eq!(result.added, vec!["mcp-new"]);
    assert_eq!(result.skipped, vec!["mcp-github"]);

    let plugins = read_allowed_plugins(&claude_dir);
    assert!(plugins.contains(&"mcp-github".to_string()));
    assert!(plugins.contains(&"mcp-existing".to_string()));
    assert!(plugins.contains(&"mcp-new".to_string()));
}

#[test]
fn test_enable_activates_plugins_no_plugins_field() {
    let tmp = TempDir::new().unwrap();
    let claude_dir = tmp.path().join(".claude");
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_skill_yaml(&skill_dir, &[]);

    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let result = activate_plugins(&yaml, &claude_dir).unwrap();

    assert!(result.added.is_empty());
    assert!(result.skipped.is_empty());
    // settings.json should NOT be created when there are no plugins
    assert!(!claude_dir.join("settings.json").exists());
}

#[test]
fn test_enable_activates_plugins_settings_without_allowed_plugins_key() {
    let tmp = TempDir::new().unwrap();
    let claude_dir = tmp.path().join(".claude");
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_skill_yaml(&skill_dir, &["mcp-jira"]);
    // settings.json exists but has no allowedPlugins key
    make_settings_json(&claude_dir, r#"{"mcpServers":{}}"#);

    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let result = activate_plugins(&yaml, &claude_dir).unwrap();

    assert_eq!(result.added, vec!["mcp-jira"]);
    let plugins = read_allowed_plugins(&claude_dir);
    assert!(plugins.contains(&"mcp-jira".to_string()));
}

#[test]
fn test_enable_activates_plugins_all_already_present() {
    let tmp = TempDir::new().unwrap();
    let claude_dir = tmp.path().join(".claude");
    let skill_dir = tmp.path().join("my-skill");
    fs::create_dir(&skill_dir).unwrap();
    make_skill_yaml(&skill_dir, &["mcp-github"]);
    make_settings_json(&claude_dir, r#"{"allowedPlugins":["mcp-github"]}"#);

    let yaml = fs::read_to_string(skill_dir.join("skill.yaml")).unwrap();
    let result = activate_plugins(&yaml, &claude_dir).unwrap();

    assert!(result.added.is_empty());
    assert_eq!(result.skipped, vec!["mcp-github"]);
    // File content unchanged structurally
    let plugins = read_allowed_plugins(&claude_dir);
    assert_eq!(plugins, vec!["mcp-github"]);
}
