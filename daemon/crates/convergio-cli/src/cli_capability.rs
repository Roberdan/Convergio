use crate::cli_error::CliError;
use clap::Subcommand;

const DEFAULT_API: &str = "http://127.0.0.1:8420";

#[derive(Debug, Subcommand)]
pub enum CapabilityCommands {
    /// List registered capabilities (cvg capability list [--ring 2])
    List {
        #[arg(long)]
        ring: Option<u8>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        #[arg(long)]
        human: bool,
    },
    /// Invoke a capability (cvg capability invoke <name> <input-json>)
    Invoke {
        name: String,
        input: String,
        #[arg(long)]
        agent: Option<String>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Register a capability from YAML (cvg capability register <path>)
    Register {
        path: String,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Manage per-agent permissions (cvg capability permissions <agent>)
    Permissions {
        agent: String,
        #[arg(long)]
        grant: Option<String>,
        #[arg(long)]
        revoke: Option<String>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Show schema for a capability (cvg capability schema <name>)
    Schema {
        name: String,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        #[arg(long)]
        human: bool,
    },
}

pub async fn handle(cmd: CapabilityCommands) -> Result<(), CliError> {
    match cmd {
        CapabilityCommands::List { ring, api_url, human } => {
            let qs = ring.map(|r| format!("?ring={r}")).unwrap_or_default();
            crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/capabilities/list{qs}"),
                human,
            ).await
        }
        CapabilityCommands::Invoke { name, input, agent, api_url } => {
            let parsed: serde_json::Value = serde_json::from_str(&input)
                .map_err(|e| CliError::ApiCallFailed(format!("invalid JSON input: {e}")))?;
            let body = serde_json::json!({
                "name": name,
                "input": parsed,
                "agent_id": agent.unwrap_or_else(|| "cli".to_string()),
            });
            let url = format!("{api_url}/api/capabilities/invoke");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        CapabilityCommands::Register { path, api_url } => {
            let body = serde_json::json!({"path": path});
            let url = format!("{api_url}/api/capabilities/register");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        CapabilityCommands::Permissions { agent, grant, revoke, api_url } => {
            let body = serde_json::json!({
                "agent_id": agent,
                "grant": grant,
                "revoke": revoke,
            });
            let url = format!("{api_url}/api/capabilities/permissions");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        CapabilityCommands::Schema { name, api_url, human } => {
            crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/capabilities/schema/{name}"),
                human,
            ).await
        }
    }
}
