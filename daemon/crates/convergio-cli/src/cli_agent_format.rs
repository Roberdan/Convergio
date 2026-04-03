// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Agent command dispatch + transpile logic — extracted from cli_agent.rs (Plan F, T4-02).

use crate::cli_agent::AgentCommands;
use crate::cli_error::CliError;

pub(crate) async fn dispatch(cmd: AgentCommands) -> Result<(), CliError> {
    match cmd {
        AgentCommands::Transpile {
            name,
            provider,
            api_url,
        } => {
            handle_transpile(&name, &provider, &api_url).await?;
        }
        AgentCommands::Start {
            name,
            task_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "agent_id": name,
                "name": name,
                "task_id": task_id,
            });
            crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/agent/start"),
                &body,
                human,
            )
            .await?;
        }
        AgentCommands::Complete {
            agent_id,
            summary,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "agent_id": agent_id,
                "summary": summary,
            });
            crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/agent/complete"),
                &body,
                human,
            )
            .await?;
        }
        AgentCommands::List { human, api_url } => {
            crate::cli_http::fetch_and_print(&format!("{api_url}/api/agents"), human).await?;
        }
        AgentCommands::Sync {
            source_dir,
            human,
            api_url,
        } => {
            let body = serde_json::json!({"source_dir": source_dir});
            crate::cli_http::post_and_print(&format!("{api_url}/api/agents/sync"), &body, human)
                .await?;
        }
        AgentCommands::Enable {
            name,
            target_dir,
            human,
            api_url,
        } => {
            let dir = target_dir.unwrap_or_else(|| ".github/agents".to_string());
            let body = serde_json::json!({"name": name, "target_dir": dir});
            crate::cli_http::post_and_print(&format!("{api_url}/api/agents/enable"), &body, human)
                .await?;
        }
        AgentCommands::Disable {
            name,
            target_dir,
            human,
            api_url,
        } => {
            let dir = target_dir.unwrap_or_else(|| ".github/agents".to_string());
            let body = serde_json::json!({"name": name, "target_dir": dir});
            crate::cli_http::post_and_print(&format!("{api_url}/api/agents/disable"), &body, human)
                .await?;
        }
        AgentCommands::Catalog {
            category,
            human,
            api_url,
        } => {
            let url = if let Some(cat) = category {
                format!("{api_url}/api/agents/catalog?category={cat}")
            } else {
                format!("{api_url}/api/agents/catalog")
            };
            crate::cli_http::fetch_and_print(&url, human).await?;
        }
        AgentCommands::Triage {
            description,
            domain,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "problem_description": description,
                "domain": domain,
            });
            crate::cli_http::post_and_print(&format!("{api_url}/api/agents/triage"), &body, human)
                .await?;
        }
        AgentCommands::History {
            since,
            until,
            status,
            model,
            limit,
            api_url,
        } => {
            crate::cli_agent_history::handle_history(&api_url, since, until, status, model, limit)
                .await?;
        }
        AgentCommands::Create {
            name,
            category,
            description,
            model,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "name": name, "category": category,
                "description": description, "model": model,
            });
            crate::cli_http::post_and_print(&format!("{api_url}/api/agents/create"), &body, human)
                .await?;
        }
    }
    Ok(())
}

async fn handle_transpile(name: &str, provider: &str, api_url: &str) -> Result<(), CliError> {
    let enc: String = name
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.' {
                c.to_string()
            } else {
                format!("%{:02X}", c as u32)
            }
        })
        .collect();
    let url = format!("{api_url}/api/agents/catalog?name={enc}");
    let resp = reqwest::get(&url)
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    let val: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
    let agent = if val.is_array() {
        val.as_array().and_then(|a| a.first()).cloned()
    } else {
        Some(val)
    };
    let agent =
        agent.ok_or_else(|| CliError::NotFound(format!("agent '{name}' not found in catalog")))?;
    let desc = agent["description"].as_str().unwrap_or("");
    let model = agent["model"].as_str().unwrap_or("claude-sonnet-4-6");
    let tools = agent["tools"].as_str().unwrap_or("view,edit,bash");
    let output = match provider {
        "claude-code" => crate::transpiler::transpile_claude_code(name, desc, model, tools),
        "copilot-cli" => crate::transpiler::transpile_copilot_cli(name, desc, model, tools),
        "generic-llm" => crate::transpiler::transpile_generic_llm(name, desc, model),
        other => {
            return Err(CliError::InvalidInput(format!(
                "unknown provider '{other}'; use: claude-code, copilot-cli, generic-llm"
            )));
        }
    };
    print!("{output}");
    Ok(())
}
