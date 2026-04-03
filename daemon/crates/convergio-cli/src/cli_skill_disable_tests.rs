// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_skill_disable — shared-dependency check for plugins and agents.

use super::deactivate_plugins;
use std::fs;
use tempfile::TempDir;

// --- Helpers -----------------------------------------------------------------

fn write_skill_yaml(dir: &std::path::Path, name: &str, plugins: &[&str]) {
    let plugin_list = if plugins.is_empty() {
        String::new()
    } else {
        format!("requires-plugins: [{}]\n", plugins.join(", "))
    };
    let yaml = format!(
        "name: {name}\nversion: 1.0.0\ndescription: A skill\ndomain: testing\n\
         constitution-version: 2.0.0\nlicense: MPL-2.0\ncopyright: Roberto D'Angelo, 2026\n{plugin_list}"
    );
    fs::create_dir_all(dir).unwrap();
    fs::write(dir.join("skill.yaml"), yaml).unwrap();
}

fn write_settings_json(claude_dir: &std::path::Path, plugins: &[&str]) {
    fs::create_dir_all(claude_dir).unwrap();
    let arr: Vec<serde_json::Value> = plugins
        .iter()
        .map(|p| serde_json::Value::String((*p).to_string()))
        .collect();
    let val = serde_json::json!({ "allowedPlugins": arr });
    fs::write(
        claude_dir.join("settings.json"),
        serde_json::to_string_pretty(&val).unwrap(),
    )
    .unwrap();
}

fn read_allowed_plugins(claude_dir: &std::path::Path) -> Vec<String> {
    let text = fs::read_to_string(claude_dir.join("settings.json")).unwrap();
    let val: serde_json::Value = serde_json::from_str(&text).unwrap();
    val["allowedPlugins"]
        .as_array()
        .unwrap_or(&vec![])
        .iter()
        .filter_map(|v| v.as_str().map(String::from))
        .collect()
}

// --- Tests -------------------------------------------------------------------

/// A skill's unique plugin is removed from allowedPlugins after disable.
#[test]
fn test_disable_removes_unshared() {
    let tmp = TempDir::new().unwrap();
    let skills_dir = tmp.path().join("skills");

    // skill-a requires mcp-unique (only skill in directory)
    let skill_a_dir = skills_dir.join("skill-a");
    write_skill_yaml(&skill_a_dir, "skill-a", &["mcp-unique"]);

    let claude_dir = tmp.path().join(".claude");
    write_settings_json(&claude_dir, &["mcp-unique"]);

    let yaml = fs::read_to_string(skill_a_dir.join("skill.yaml")).unwrap();
    let result = deactivate_plugins(&yaml, &skills_dir, "skill-a", &claude_dir).unwrap();

    assert!(
        result.disabled_plugins.contains(&"mcp-unique".to_string()),
        "mcp-unique should be disabled: {:?}",
        result
    );
    assert!(
        result.kept_shared.is_empty(),
        "nothing shared: {:?}",
        result
    );

    let remaining = read_allowed_plugins(&claude_dir);
    assert!(
        !remaining.contains(&"mcp-unique".to_string()),
        "mcp-unique must be removed from settings.json: {remaining:?}"
    );
}

/// A plugin shared with another active skill is kept in allowedPlugins.
#[test]
fn test_disable_keeps_shared() {
    let tmp = TempDir::new().unwrap();
    let skills_dir = tmp.path().join("skills");

    // skill-a requires mcp-shared (being disabled)
    let skill_a_dir = skills_dir.join("skill-a");
    write_skill_yaml(&skill_a_dir, "skill-a", &["mcp-shared"]);

    // skill-b also requires mcp-shared — so the plugin is shared
    let skill_b_dir = skills_dir.join("skill-b");
    write_skill_yaml(&skill_b_dir, "skill-b", &["mcp-shared"]);

    let claude_dir = tmp.path().join(".claude");
    write_settings_json(&claude_dir, &["mcp-shared"]);

    let yaml = fs::read_to_string(skill_a_dir.join("skill.yaml")).unwrap();
    let result = deactivate_plugins(&yaml, &skills_dir, "skill-a", &claude_dir).unwrap();

    assert!(
        result.kept_shared.contains(&"mcp-shared".to_string()),
        "mcp-shared should be kept (shared): {:?}",
        result
    );
    assert!(
        result.disabled_plugins.is_empty(),
        "nothing disabled: {:?}",
        result
    );

    let remaining = read_allowed_plugins(&claude_dir);
    assert!(
        remaining.contains(&"mcp-shared".to_string()),
        "mcp-shared must remain in settings.json: {remaining:?}"
    );
}
