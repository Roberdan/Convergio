// CLI wrappers: `cvg claude <name>` and `cvg copilot <name>`.
// Registers the agent with the daemon, launches the AI tool, deregisters on exit.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum LaunchCommands {
    /// Launch a claude session with auto-registration
    Claude {
        /// Agent name (used for IPC registration)
        name: String,
        /// Parent agent name (for parentage tree)
        #[arg(long)]
        parent: Option<String>,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Launch a copilot session with auto-registration
    Copilot {
        /// Agent name (used for IPC registration)
        name: String,
        /// Parent agent name (for parentage tree)
        #[arg(long)]
        parent: Option<String>,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

fn hostname() -> String {
    hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown".into())
}

async fn register_agent(
    api_url: &str,
    name: &str,
    agent_type: &str,
    parent: Option<&str>,
) -> Result<(), CliError> {
    let host = hostname();
    let pid = std::process::id();
    let mut body = serde_json::json!({
        "agent_id": name,
        "host": host,
        "agent_type": agent_type,
        "pid": pid,
    });
    if let Some(p) = parent {
        body["parent_agent"] = serde_json::json!(p);
    }
    let client = reqwest::Client::new();
    let url = format!("{api_url}/api/ipc/agents/register");
    match client.post(&url).json(&body).send().await {
        Ok(resp) if resp.status().is_success() => {
            eprintln!("✓ registered {name}@{host} (type={agent_type})");
            Ok(())
        }
        Ok(resp) => {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            eprintln!("⚠ registration returned {status}: {text}");
            Ok(()) // non-fatal: proceed with launch
        }
        Err(e) => {
            eprintln!("⚠ daemon unreachable ({e}), launching without registration");
            Ok(())
        }
    }
}

async fn deregister_agent(api_url: &str, name: &str) {
    let host = hostname();
    let body = serde_json::json!({
        "agent_id": name,
        "host": host,
    });
    let client = reqwest::Client::new();
    let url = format!("{api_url}/api/ipc/agents/unregister");
    match client.post(&url).json(&body).send().await {
        Ok(_) => eprintln!("✓ deregistered {name}@{host}"),
        Err(e) => eprintln!("⚠ deregister failed: {e}"),
    }
}

async fn launch_tool(
    api_url: &str,
    name: &str,
    agent_type: &str,
    parent: Option<&str>,
    command: &str,
    args: &[&str],
) -> Result<(), CliError> {
    register_agent(api_url, name, agent_type, parent).await?;

    let mut cmd = build_launch_command(api_url, name, command, args);
    let status = cmd.status().await;

    deregister_agent(api_url, name).await;

    match status {
        Ok(s) if s.success() => Ok(()),
        Ok(s) => {
            let code = s.code().unwrap_or(1);
            Err(CliError::ApiCallFailed(format!(
                "{command} exited with code {code}"
            )))
        }
        Err(e) => Err(CliError::ApiCallFailed(format!(
            "failed to launch {command}: {e}"
        ))),
    }
}

fn build_launch_command(
    api_url: &str,
    name: &str,
    command: &str,
    args: &[&str],
) -> tokio::process::Command {
    let mut cmd = tokio::process::Command::new(command);
    cmd.args(args)
        .env("CONVERGIO_AGENT_NAME", name)
        .env("CONVERGIO_API_URL", api_url)
        .stdin(std::process::Stdio::inherit())
        .stdout(std::process::Stdio::inherit())
        .stderr(std::process::Stdio::inherit());
    cmd
}

pub async fn handle(cmd: LaunchCommands) -> Result<(), CliError> {
    match cmd {
        LaunchCommands::Claude {
            name,
            parent,
            api_url,
        } => {
            launch_tool(
                &api_url,
                &name,
                "claude",
                parent.as_deref(),
                "claude",
                &[],
            )
            .await
        }
        LaunchCommands::Copilot {
            name,
            parent,
            api_url,
        } => {
            launch_tool(
                &api_url,
                &name,
                "copilot",
                parent.as_deref(),
                "gh",
                &["copilot"],
            )
            .await
        }
    }
}

#[cfg(test)]
mod tests {
    use super::build_launch_command;

    #[test]
    fn launch_command_sets_agent_env_vars() {
        let cmd = build_launch_command("http://localhost:8420", "priya", "echo", &["ok"]);
        let envs: Vec<(String, String)> = cmd
            .as_std()
            .get_envs()
            .filter_map(|(k, v)| Some((k.to_string_lossy().to_string(), v?.to_string_lossy().to_string())))
            .collect();
        assert!(envs.iter().any(|(k, v)| k == "CONVERGIO_AGENT_NAME" && v == "priya"));
        assert!(envs.iter().any(|(k, v)| k == "CONVERGIO_API_URL" && v == "http://localhost:8420"));
    }
}
