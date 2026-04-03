// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Skill disable subcommand — removes unshared plugins/agents when a skill is disabled.

use crate::cli_error::CliError;
use crate::cli_skill_validate::{agent_name_valid, yaml_get_list};
use crate::message_error::MessageResult;
use std::path::{Path, PathBuf};

/// Result of deactivating plugins for a disabled skill.
#[derive(Debug)]
pub struct DeactivatePluginsResult {
    /// Plugins removed from allowedPlugins (not required by any other skill).
    pub disabled_plugins: Vec<String>,
    /// Agents disabled via daemon API.
    pub disabled_agents: Vec<String>,
    /// Plugins kept because another active skill also requires them.
    pub kept_shared: Vec<String>,
}

/// Collect all plugins required by skills OTHER than `disabled_skill_name`.
/// Scans every skill.yaml in `skills_dir` subdirectories, skipping the one being disabled.
fn collect_other_skills_plugins(skills_dir: &Path, disabled_skill_name: &str) -> Vec<String> {
    let mut other_plugins: Vec<String> = Vec::new();
    let entries = match std::fs::read_dir(skills_dir) {
        Ok(e) => e,
        Err(_) => return other_plugins,
    };
    for entry in entries.flatten() {
        if !entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
            continue;
        }
        let dir_name = entry.file_name();
        let dir_str = dir_name.to_string_lossy();
        if dir_str == disabled_skill_name {
            continue; // skip the skill being disabled
        }
        let yaml_path = entry.path().join("skill.yaml");
        if let Ok(content) = std::fs::read_to_string(&yaml_path) {
            if let Some(plugins) = yaml_get_list(&content, "requires-plugins") {
                other_plugins.extend(plugins);
            }
        }
    }
    other_plugins
}

/// Remove plugins that are no longer needed from .claude/settings.json allowedPlugins.
/// Returns which were removed and which were kept (shared with other skills).
pub fn deactivate_plugins(
    yaml_content: &str,
    skills_dir: &Path,
    disabled_skill_name: &str,
    claude_dir: &Path,
) -> MessageResult<DeactivatePluginsResult> {
    let plugins = yaml_get_list(yaml_content, "requires-plugins").unwrap_or_default();
    if plugins.is_empty() {
        return Ok(DeactivatePluginsResult {
            disabled_plugins: vec![],
            disabled_agents: vec![],
            kept_shared: vec![],
        });
    }

    let other_plugins = collect_other_skills_plugins(skills_dir, disabled_skill_name);

    let mut to_remove: Vec<String> = Vec::new();
    let mut kept_shared: Vec<String> = Vec::new();
    for plugin in &plugins {
        if other_plugins.contains(plugin) {
            kept_shared.push(plugin.clone());
        } else {
            to_remove.push(plugin.clone());
        }
    }

    if !to_remove.is_empty() {
        let settings_path = claude_dir.join("settings.json");
        if settings_path.is_file() {
            let raw = std::fs::read_to_string(&settings_path)
                .map_err(|e| format!("read {}: {e}", settings_path.display()))?;
            let mut settings: serde_json::Value = serde_json::from_str(&raw)
                .map_err(|e| format!("parse {}: {e}", settings_path.display()))?;

            if let Some(arr) = settings
                .get_mut("allowedPlugins")
                .and_then(|v| v.as_array_mut())
            {
                arr.retain(|v| {
                    v.as_str()
                        .map(|s| !to_remove.contains(&s.to_string()))
                        .unwrap_or(true)
                });
            }

            let pretty = serde_json::to_string_pretty(&settings)
                .map_err(|e| format!("serialize settings: {e}"))?;
            std::fs::write(&settings_path, pretty)
                .map_err(|e| format!("write {}: {e}", settings_path.display()))?;
        }
    }

    Ok(DeactivatePluginsResult {
        disabled_plugins: to_remove,
        disabled_agents: vec![], // populated by async handle()
        kept_shared,
    })
}

/// Disable a skill: removes unshared plugins and disables unshared agents via daemon API.
pub async fn handle(skill_dir: &Path, api_url: &str, human: bool) -> Result<(), CliError> {
    let yaml_path = skill_dir.join("skill.yaml");
    if !yaml_path.is_file() {
        return Err(CliError::InvalidInput(format!(
            "skill.yaml not found in {}",
            skill_dir.display()
        )));
    }
    let yaml_content = std::fs::read_to_string(&yaml_path)
        .map_err(|e| CliError::InvalidInput(format!("read error: {e}")))?;

    let skill_name = skill_dir
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();

    // Determine skills_dir as parent of skill_dir
    let skills_dir = skill_dir
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."));

    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("/tmp"));
    let claude_dir = home.join(".claude");

    let mut plugin_result =
        match deactivate_plugins(&yaml_content, &skills_dir, &skill_name, &claude_dir) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("warning: plugin deactivation failed: {e}");
                DeactivatePluginsResult {
                    disabled_plugins: vec![],
                    disabled_agents: vec![],
                    kept_shared: vec![],
                }
            }
        };

    // Disable agents not shared with other active skills
    let agents = yaml_get_list(&yaml_content, "requires-agents").unwrap_or_default();
    let other_agent_plugins: Vec<String> = {
        let entries = match std::fs::read_dir(&skills_dir) {
            Ok(e) => Some(e),
            Err(e) => {
                eprintln!("warn: could not read skills directory: {e}");
                None
            }
        };
        let mut v = Vec::new();
        if let Some(entries) = entries {
            for entry in entries.flatten() {
                if !entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    continue;
                }
                if entry.file_name().to_string_lossy() == skill_name {
                    continue;
                }
                let yp = entry.path().join("skill.yaml");
                if let Ok(c) = std::fs::read_to_string(&yp) {
                    if let Some(a) = yaml_get_list(&c, "requires-agents") {
                        v.extend(a);
                    }
                }
            }
        }
        v
    };

    for agent_name in &agents {
        if !agent_name_valid(agent_name) {
            eprintln!("warning: skipping invalid agent name '{agent_name}'");
            continue;
        }
        if other_agent_plugins.contains(agent_name) {
            plugin_result.kept_shared.push(agent_name.clone());
            continue;
        }
        let body = serde_json::json!({"name": agent_name});
        let url = format!("{api_url}/api/agents/disable");
        match reqwest::Client::new().post(&url).json(&body).send().await {
            Ok(resp) if resp.status().is_success() => {
                plugin_result.disabled_agents.push(agent_name.clone());
                if human {
                    println!("disabled agent: {agent_name}");
                }
            }
            Ok(resp) => {
                let status = resp.status();
                let text = resp.text().await.unwrap_or_default();
                eprintln!("warning: failed to disable agent '{agent_name}': {status} {text}");
            }
            Err(e) => {
                eprintln!("warning: failed to disable agent '{agent_name}': {e}");
            }
        }
    }

    if human {
        for p in &plugin_result.disabled_plugins {
            println!("removed plugin: {p}");
        }
        for p in &plugin_result.kept_shared {
            println!("kept shared: {p}");
        }
        println!(
            "\nSummary: {} plugins removed, {} agents disabled, {} kept (shared)",
            plugin_result.disabled_plugins.len(),
            plugin_result.disabled_agents.len(),
            plugin_result.kept_shared.len(),
        );
    } else {
        println!(
            "{}",
            serde_json::json!({
                "ok": true,
                "disabled_plugins": plugin_result.disabled_plugins,
                "disabled_agents": plugin_result.disabled_agents,
                "kept_shared": plugin_result.kept_shared,
            })
        );
    }
    Ok(())
}

#[cfg(test)]
#[path = "cli_skill_disable_tests.rs"]
mod tests;
