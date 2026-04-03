use crate::cli_error::CliError;
use serde_json::{json, Value};
use std::path::PathBuf;

const DEFAULT_TIMEOUT_SECS: u64 = 120;

pub async fn handle(
    alias: String,
    message: Option<String>,
    list: bool,
    set_alias: Option<String>,
    set_agent: Option<String>,
    api_url: &str,
) -> Result<(), CliError> {
    if list {
        return handle_list(api_url).await;
    }
    if let (Some(a), Some(agent)) = (set_alias, set_agent) {
        return handle_set(&a, &agent);
    }
    let msg = message.ok_or_else(|| {
        CliError::InvalidInput("Usage: cvg ask <alias> \"message\"".into())
    })?;
    let agent_name = resolve_alias(&alias, api_url).await?;
    run_ask("user", &agent_name, &msg, DEFAULT_TIMEOUT_SECS, api_url).await;
    Ok(())
}

fn aliases_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".convergio")
        .join("aliases.toml")
}

fn load_aliases() -> std::collections::HashMap<String, String> {
    let path = aliases_path();
    let content = match std::fs::read_to_string(&path) {
        Ok(c) => c,
        Err(_) => return std::collections::HashMap::new(),
    };
    let table: toml::Value = match content.parse() {
        Ok(v) => v,
        Err(_) => return std::collections::HashMap::new(),
    };
    let mut map = std::collections::HashMap::new();
    if let Some(aliases) = table.get("aliases").and_then(|v| v.as_table()) {
        for (k, v) in aliases {
            if let Some(s) = v.as_str() {
                map.insert(k.clone(), s.to_string());
            }
        }
    }
    map
}

async fn resolve_alias(alias: &str, api_url: &str) -> Result<String, CliError> {
    let aliases = load_aliases();
    if let Some(agent) = aliases.get(alias) {
        return Ok(agent.clone());
    }
    // Try prefix match against agent catalog
    if let Ok(agents) = fetch_catalog_agents(api_url).await {
        for name in &agents {
            if name.starts_with(alias) {
                return Ok(name.clone());
            }
        }
    }
    // Fallback: use alias as-is (might be a full agent name)
    Ok(alias.to_string())
}

async fn fetch_catalog_agents(api_url: &str) -> Result<Vec<String>, CliError> {
    let client = reqwest::Client::new();
    let url = format!("{api_url}/api/ipc/agents/list");
    let resp = client
        .get(&url)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("{e}")))?;
    let data: Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("{e}")))?;
    let mut names = Vec::new();
    if let Some(agents) = data.get("agents").and_then(|v| v.as_array()) {
        for a in agents {
            if let Some(id) = a.get("agent_id").and_then(|v| v.as_str()) {
                names.push(id.to_string());
            }
        }
    }
    Ok(names)
}

async fn handle_list(api_url: &str) -> Result<(), CliError> {
    let aliases = load_aliases();
    println!("\x1b[1mConfigured aliases:\x1b[0m");
    if aliases.is_empty() {
        println!("  (none — run cvg setup to generate defaults)");
    } else {
        let mut sorted: Vec<_> = aliases.iter().collect();
        sorted.sort_by_key(|(k, _)| (*k).clone());
        for (alias, agent) in sorted {
            println!("  \x1b[36m{alias:12}\x1b[0m → {agent}");
        }
    }
    // Also show active agents
    if let Ok(agents) = fetch_catalog_agents(api_url).await {
        if !agents.is_empty() {
            println!("\n\x1b[1mActive agents (direct name also works):\x1b[0m");
            for name in &agents {
                let aliased = aliases.values().any(|v| v == name);
                let marker = if aliased { " (aliased)" } else { "" };
                println!("  \x1b[2m{name}{marker}\x1b[0m");
            }
        }
    }
    Ok(())
}

fn handle_set(alias: &str, agent: &str) -> Result<(), CliError> {
    let path = aliases_path();
    let content = std::fs::read_to_string(&path).unwrap_or_default();
    let mut table: toml::Value = content
        .parse()
        .unwrap_or_else(|_| toml::Value::Table(toml::map::Map::new()));
    let aliases = table
        .as_table_mut()
        .unwrap()
        .entry("aliases")
        .or_insert_with(|| toml::Value::Table(toml::map::Map::new()))
        .as_table_mut()
        .ok_or_else(|| CliError::InvalidInput("corrupt aliases.toml".into()))?;
    aliases.insert(alias.to_string(), toml::Value::String(agent.to_string()));
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(CliError::Io)?;
    }
    std::fs::write(&path, table.to_string()).map_err(CliError::Io)?;
    println!("Alias set: {alias} → {agent}");
    Ok(())
}

async fn run_ask(from: &str, to: &str, message: &str, timeout_secs: u64, api_url: &str) {
    let client = reqwest::Client::new();
    let body = json!({
        "from": from,
        "to": to,
        "message": message,
        "timeout_secs": timeout_secs
    });
    let url = format!("{api_url}/api/ipc/ask");
    match client.post(&url).json(&body).send().await {
        Ok(resp) => match resp.json::<Value>().await {
            Ok(payload) => match parse_response(&payload) {
                Ok(reply) => println!("{reply}"),
                Err(err) => eprintln!("error: {err}"),
            },
            Err(e) => eprintln!("error: invalid response: {e}"),
        },
        Err(e) => eprintln!("error: request failed: {e}"),
    }
}

fn parse_response(payload: &Value) -> Result<String, String> {
    if payload.get("ok").and_then(Value::as_bool) == Some(true) {
        let reply = payload
            .get("reply")
            .ok_or_else(|| "missing reply".to_string())?;
        let from = reply
            .get("from")
            .and_then(Value::as_str)
            .unwrap_or("unknown");
        let content = reply
            .get("content")
            .and_then(Value::as_str)
            .unwrap_or_default();
        return Ok(format!("\x1b[32m\x1b[1m{from}\x1b[0m: {content}"));
    }
    let code = payload
        .get("error")
        .and_then(|e| e.get("code"))
        .and_then(Value::as_str)
        .unwrap_or("ERROR");
    let msg = payload
        .get("error")
        .and_then(|e| e.get("message"))
        .and_then(Value::as_str)
        .unwrap_or("request failed");
    Err(format!("{code}: {msg}"))
}

pub fn generate_default_aliases() -> String {
    r#"[aliases]
baccio = "baccio-tech-architect"
rex = "rex-code-reviewer"
ali = "ali-chief-of-staff"
otto = "otto-performance-optimizer"
luca = "luca-security-expert"
sara = "sara-ux-ui-designer"
paolo = "paolo-best-practices-enforcer"
marco = "marco-devops-engineer"
omri = "omri-data-scientist"
"#
    .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn parse_successful_reply() {
        let payload = json!({
            "ok": true,
            "reply": { "from": "baccio", "content": "Analysis complete." }
        });
        let result = parse_response(&payload).unwrap();
        assert!(result.contains("baccio"));
        assert!(result.contains("Analysis complete."));
    }

    #[test]
    fn parse_error_reply() {
        let payload = json!({
            "ok": false,
            "error": { "code": "TIMEOUT", "message": "No reply within 120s" }
        });
        let err = parse_response(&payload).unwrap_err();
        assert!(err.contains("TIMEOUT"));
    }

    #[test]
    fn generate_defaults_has_all_aliases() {
        let content = generate_default_aliases();
        assert!(content.contains("baccio"));
        assert!(content.contains("rex"));
        assert!(content.contains("ali"));
        assert!(content.contains("otto"));
        assert!(content.contains("luca"));
    }
}
