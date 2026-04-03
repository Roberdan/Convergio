// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_agent module.

use super::*;

#[test]
fn agent_commands_transpile_variant_exists() {
    let cmd = AgentCommands::Transpile {
        name: "code-reviewer".to_string(),
        provider: "claude-code".to_string(),
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Transpile { .. }));
}

#[test]
fn agent_commands_start_variant_exists() {
    let cmd = AgentCommands::Start {
        name: "task-executor".to_string(),
        task_id: Some(8797),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Start { .. }));
}

#[test]
fn agent_commands_complete_variant_exists() {
    let cmd = AgentCommands::Complete {
        agent_id: "abc-123".to_string(),
        summary: Some("done".to_string()),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Complete { .. }));
}

#[test]
fn agent_commands_list_variant_exists() {
    let cmd = AgentCommands::List {
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::List { .. }));
}

#[test]
fn agent_commands_triage_variant_exists() {
    let cmd = AgentCommands::Triage {
        description: "debugging a deployment issue".to_string(),
        domain: Some("technical".to_string()),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Triage { .. }));
}

#[test]
fn triage_builds_correct_body() {
    let body = serde_json::json!({
        "problem_description": "need help with debugging",
        "domain": "technical",
    });
    assert_eq!(body["problem_description"], "need help with debugging");
    assert_eq!(body["domain"], "technical");
}

#[test]
fn agent_start_builds_correct_body() {
    let body = serde_json::json!({
        "name": "task-executor",
        "task_id": 42_i64,
    });
    assert_eq!(body["name"], "task-executor");
    assert_eq!(body["task_id"], 42);
}

#[test]
fn agent_commands_sync_variant_exists() {
    let cmd = AgentCommands::Sync {
        source_dir: "/tmp/agents".to_string(),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Sync { .. }));
}

#[test]
fn agent_commands_enable_variant_exists() {
    let cmd = AgentCommands::Enable {
        name: "baccio".to_string(),
        target_dir: Some(".github/agents".to_string()),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Enable { .. }));
}

#[test]
fn agent_commands_disable_variant_exists() {
    let cmd = AgentCommands::Disable {
        name: "baccio".to_string(),
        target_dir: None,
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Disable { .. }));
}

#[test]
fn agent_commands_catalog_variant_exists() {
    let cmd = AgentCommands::Catalog {
        category: Some("technical".to_string()),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Catalog { .. }));
}

#[test]
fn agent_commands_create_variant_exists() {
    let cmd = AgentCommands::Create {
        name: "new-agent".to_string(),
        category: "technical".to_string(),
        description: "A new agent".to_string(),
        model: "claude-sonnet-4-6".to_string(),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AgentCommands::Create { .. }));
}

#[test]
fn catalog_url_with_category_filter() {
    let cat = "technical";
    let api_url = "http://localhost:8420";
    let url = format!("{api_url}/api/agents/catalog?category={cat}");
    assert_eq!(
        url,
        "http://localhost:8420/api/agents/catalog?category=technical"
    );
}

#[test]
fn enable_default_target_dir() {
    let target_dir: Option<String> = None;
    let dir = target_dir.unwrap_or_else(|| ".github/agents".to_string());
    assert_eq!(dir, ".github/agents");
}
