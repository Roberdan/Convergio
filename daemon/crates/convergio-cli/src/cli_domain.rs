// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Domain-skill mapping CLI subcommands: `cvg domain list` and `cvg domain map`.
// Pure HTTP client — delegates all operations to daemon API.

use crate::message_error::MessageResult;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum DomainCommands {
    /// List all domain→skill mappings
    List {
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
        /// Human-readable table output instead of JSON
        #[arg(long)]
        human: bool,
    },
    /// Add a domain→skill mapping
    Map {
        /// Domain name (e.g. healthcare)
        domain: String,
        /// Skill name — must match an existing claude-config/skills/<skill>/ directory
        skill: String,
        /// Optional description
        #[arg(long)]
        description: Option<String>,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
    },
}

pub async fn dispatch(cmd: DomainCommands) -> Result<(), crate::cli_error::CliError> {
    match cmd {
        DomainCommands::List { api_url, human } => handle_list(&api_url, human).await,
        DomainCommands::Map {
            domain,
            skill,
            description,
            api_url,
            human,
        } => handle_map(&domain, &skill, description.as_deref(), &api_url, human).await?,
    }
    Ok(())
}

async fn handle_list(api_url: &str, human: bool) {
    if let Err(e) =
        crate::cli_http::fetch_and_print(&format!("{api_url}/api/domain/list"), human).await
    {
        eprintln!("error: {e}");
    }
}

async fn handle_map(
    domain: &str,
    skill: &str,
    description: Option<&str>,
    api_url: &str,
    human: bool,
) -> Result<(), crate::cli_error::CliError> {
    // Validate skill directory exists before calling daemon (fast-fail at CLI layer)
    let skill_path = format!("claude-config/skills/{skill}");
    validate_skill_dir(&skill_path)
        .map_err(|e| crate::cli_error::CliError::InvalidInput(format!("error: {e}")))?;
    let body = serde_json::json!({
        "domain": domain,
        "skill_name": skill,
        "description": description,
    });
    if let Err(e) =
        crate::cli_http::post_and_print(&format!("{api_url}/api/domain/map"), &body, human).await
    {
        eprintln!("error: {e}");
    }
    Ok(())
}

/// Validate that the skill directory exists at `path`.
pub(crate) fn validate_skill_dir(path: &str) -> MessageResult<()> {
    if std::path::Path::new(path).is_dir() {
        Ok(())
    } else {
        Err(format!("skill directory does not exist: {path}").into())
    }
}
