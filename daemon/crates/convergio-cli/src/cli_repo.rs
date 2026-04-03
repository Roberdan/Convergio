// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Repository CLI subcommands: add, list, show, link, sync.
// Delegates to daemon HTTP API at /api/repositories.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum RepoCommands {
    /// Register a repository in the platform
    Add {
        /// Short unique name for the repository (e.g. convergio-platform)
        name: String,
        /// Absolute filesystem path to the repository root
        #[arg(long)]
        path: String,
        /// Optional GitHub URL (e.g. https://github.com/org/repo)
        #[arg(long)]
        github_url: Option<String>,
        /// Optional description
        #[arg(long)]
        description: Option<String>,
        /// Transport type: local | ssh | tailscale (default: local)
        #[arg(long, default_value = "local")]
        transport: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List all registered repositories
    List {
        /// Output as JSON (default: pretty table)
        #[arg(long)]
        json: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show details for a single repository
    Show {
        /// Repository name
        name: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Link a repository to a project
    Link {
        /// Repository name
        repo_name: String,
        /// Project ID
        project_id: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Verify all registered repos exist on disk and check health
    Sync {
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: RepoCommands) -> Result<(), CliError> {
    match cmd {
        RepoCommands::Add {
            name,
            path,
            github_url,
            description,
            transport,
            api_url,
        } => handle_add(&name, &path, github_url, description, &transport, &api_url).await,
        RepoCommands::List { json, api_url } => handle_list(json, &api_url).await,
        RepoCommands::Show { name, api_url } => handle_show(&name, &api_url).await,
        RepoCommands::Link {
            repo_name,
            project_id,
            api_url,
        } => handle_link(&repo_name, &project_id, &api_url).await,
        RepoCommands::Sync { api_url } => handle_sync(&api_url).await,
    }
}

async fn handle_add(
    name: &str,
    path: &str,
    github_url: Option<String>,
    description: Option<String>,
    transport: &str,
    api_url: &str,
) -> Result<(), CliError> {
    let payload = serde_json::json!({
        "name": name,
        "path": path,
        "github_url": github_url,
        "description": description,
        "transport": transport
    });
    let url = format!("{api_url}/api/repositories");
    crate::cli_http::post_and_print(&url, &payload, true)
        .await
        .map_err(|_| CliError::ApiCallFailed(format!("failed to add repository '{name}'")))
}

async fn handle_list(as_json: bool, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/repositories");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to list repositories".into()))?;

    if as_json {
        println!(
            "{}",
            serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
        );
        return Ok(());
    }

    // Human-readable table
    let repos = val.as_array().cloned().unwrap_or_default();
    if repos.is_empty() {
        println!("No repositories registered.");
        return Ok(());
    }
    println!(
        "{:<30} {:<12} {:<12} {}",
        "NAME", "TRANSPORT", "HEALTH", "PATH"
    );
    println!("{}", "-".repeat(80));
    for r in &repos {
        let name = r["name"].as_str().unwrap_or("-");
        let transport = r["transport"].as_str().unwrap_or("local");
        let health = r["health_status"].as_str().unwrap_or("unknown");
        let path = r["path"].as_str().unwrap_or("-");
        println!("{:<30} {:<12} {:<12} {}", name, transport, health, path);
    }
    Ok(())
}

async fn handle_show(name: &str, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/repositories/{name}");
    crate::cli_http::fetch_and_print(&url, true)
        .await
        .map_err(|_| CliError::ApiCallFailed(format!("failed to show repository '{name}'")))
}

async fn handle_link(repo_name: &str, project_id: &str, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/repositories/{repo_name}/link");
    let payload = serde_json::json!({ "project_id": project_id });
    crate::cli_http::post_and_print(&url, &payload, true)
        .await
        .map_err(|_| CliError::ApiCallFailed(format!("failed to link repository '{repo_name}'")))
}

async fn handle_sync(api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/repositories");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to fetch repositories for sync".into()))?;

    let repos = val.as_array().cloned().unwrap_or_default();
    if repos.is_empty() {
        println!("No repositories to sync.");
        return Ok(());
    }

    let mut ok = 0usize;
    let mut missing = 0usize;
    for r in &repos {
        let name = r["name"].as_str().unwrap_or("?");
        let path = r["path"].as_str().unwrap_or("");
        let exists = std::path::Path::new(path).exists();
        if exists {
            println!("[OK]      {name} -> {path}");
            ok += 1;
        } else {
            eprintln!("[MISSING] {name} -> {path} (path does not exist)");
            missing += 1;
        }
    }
    println!("\nSync complete: {ok} ok, {missing} missing.");
    if missing > 0 {
        return Err(CliError::InvalidInput(format!(
            "{missing} repositor{} not found on disk",
            if missing == 1 { "y" } else { "ies" }
        )));
    }
    Ok(())
}
