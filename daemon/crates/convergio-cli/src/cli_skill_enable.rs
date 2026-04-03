// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Skill enable subcommand — reads skill.yaml, activates required agents and plugins.

use crate::cli_error::CliError;
use crate::cli_skill_validate::{agent_name_valid, yaml_get_list};
use crate::message_error::MessageResult;
use std::path::{Path, PathBuf};

/// Result of activating plugins into settings.json.
pub struct PluginActivationResult {
    pub added: Vec<String>,
    pub skipped: Vec<String>,
}

/// Read .claude/settings.json, add plugins from requires-plugins that are not already present,
/// write back. Creates the file (and parent dir) if absent. Returns counts of added/skipped.
/// If requires-plugins is empty or absent, returns Ok with empty vecs and does NOT touch disk.
pub fn activate_plugins(
    yaml_content: &str,
    claude_dir: &Path,
) -> MessageResult<PluginActivationResult> {
    let plugins = yaml_get_list(yaml_content, "requires-plugins").unwrap_or_default();
    if plugins.is_empty() {
        return Ok(PluginActivationResult {
            added: vec![],
            skipped: vec![],
        });
    }

    let settings_path = claude_dir.join("settings.json");
    let mut settings: serde_json::Value = if settings_path.is_file() {
        let raw = std::fs::read_to_string(&settings_path)
            .map_err(|e| format!("read {}: {e}", settings_path.display()))?;
        serde_json::from_str(&raw).map_err(|e| format!("parse {}: {e}", settings_path.display()))?
    } else {
        serde_json::json!({})
    };

    let allowed = settings
        .get_mut("allowedPlugins")
        .and_then(|v| v.as_array_mut());

    let mut added = Vec::new();
    let mut skipped = Vec::new();

    if let Some(arr) = allowed {
        let existing: Vec<String> = arr
            .iter()
            .filter_map(|v| v.as_str().map(String::from))
            .collect();
        for plugin in &plugins {
            if existing.contains(plugin) {
                skipped.push(plugin.clone());
            } else {
                arr.push(serde_json::Value::String(plugin.clone()));
                added.push(plugin.clone());
            }
        }
    } else {
        // Key absent or not an array — replace/create it
        let arr: Vec<serde_json::Value> = plugins
            .iter()
            .map(|p| serde_json::Value::String(p.clone()))
            .collect();
        settings["allowedPlugins"] = serde_json::Value::Array(arr);
        added = plugins.clone();
    }

    if !added.is_empty() {
        // Ensure parent dir exists (handles first-run with no .claude dir)
        if let Some(parent) = settings_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("create dir {}: {e}", parent.display()))?;
        }
        let pretty = serde_json::to_string_pretty(&settings)
            .map_err(|e| format!("serialize settings: {e}"))?;
        std::fs::write(&settings_path, pretty)
            .map_err(|e| format!("write {}: {e}", settings_path.display()))?;
    }

    Ok(PluginActivationResult { added, skipped })
}

/// Enable a skill: parse requires-agents + requires-plugins, activate agents and plugins.
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

    let agents = yaml_get_list(&yaml_content, "requires-agents").unwrap_or_default();

    let mut agents_enabled: usize = 0;
    for agent_name in &agents {
        if !agent_name_valid(agent_name) {
            eprintln!("warning: skipping invalid agent name '{agent_name}'");
            continue;
        }
        let body = serde_json::json!({"name": agent_name, "target_dir": ".github/agents"});
        let url = format!("{api_url}/api/agents/enable");
        match reqwest::Client::new().post(&url).json(&body).send().await {
            Ok(resp) if resp.status().is_success() => {
                agents_enabled += 1;
                if human {
                    println!("enabled agent: {agent_name}");
                }
            }
            Ok(resp) => {
                let status = resp.status();
                let text = resp.text().await.unwrap_or_default();
                eprintln!("warning: failed to enable agent '{agent_name}': {status} {text}");
            }
            Err(e) => {
                eprintln!("warning: failed to enable agent '{agent_name}': {e}");
            }
        }
    }

    // Activate plugins in ~/.claude/settings.json
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("/tmp"));
    let claude_dir = home.join(".claude");
    let plugin_result = match activate_plugins(&yaml_content, &claude_dir) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("warning: plugin activation failed: {e}");
            PluginActivationResult {
                added: vec![],
                skipped: vec![],
            }
        }
    };

    if human {
        for p in &plugin_result.added {
            println!("activated plugin: {p}");
        }
        for p in &plugin_result.skipped {
            println!("plugin already active (skipped): {p}");
        }
        println!(
            "\nSummary: {agents_enabled} agents enabled, {} plugins activated, {} plugins already active",
            plugin_result.added.len(),
            plugin_result.skipped.len()
        );
    } else {
        let plugins = yaml_get_list(&yaml_content, "requires-plugins").unwrap_or_default();
        println!(
            "{}",
            serde_json::json!({
                "ok": true,
                "agents_enabled": agents_enabled,
                "agents_total": agents.len(),
                "plugins_activated": plugin_result.added,
                "plugins_skipped": plugin_result.skipped,
                "plugins_total": plugins.len(),
            })
        );
    }
    Ok(())
}

#[cfg(test)]
#[path = "cli_skill_enable_tests.rs"]
mod tests;
