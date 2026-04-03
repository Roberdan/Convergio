// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Project subcommands for the cvg CLI — local filesystem ops + daemon HTTP API.

use crate::cli_error::CliError;
use clap::Subcommand;
use std::path::PathBuf;

#[derive(Debug, Subcommand)]
pub enum ProjectCommands {
    /// Create a new project with input folder and output directory
    Create {
        /// Project name
        #[arg(long)]
        name: String,
        /// Input folder path (must exist and be readable)
        #[arg(long)]
        input: PathBuf,
        /// Skip interactive confirmation
        #[arg(long)]
        yes: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List all projects as JSON
    List {
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show a single project with deliverable count
    Show {
        /// Project ID
        id: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show hierarchical plan tree for a project
    Plans {
        /// Project ID
        id: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: ProjectCommands) -> Result<(), CliError> {
    match cmd {
        ProjectCommands::Create {
            name,
            input,
            yes,
            api_url,
        } => handle_create(&name, &input, yes, &api_url).await,
        ProjectCommands::List { api_url } => handle_list(&api_url).await,
        ProjectCommands::Show { id, api_url } => handle_show(&id, &api_url).await,
        ProjectCommands::Plans { id, api_url } => handle_plans(&id, &api_url).await,
    }
}

async fn handle_list(api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/dashboard/projects");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to fetch projects".into()))?;
    println!(
        "{}",
        serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
    );
    Ok(())
}

async fn handle_create(
    name: &str,
    input: &PathBuf,
    yes: bool,
    api_url: &str,
) -> Result<(), CliError> {
    // Validate input folder exists and is readable (F-18)
    if !input.exists() {
        return Err(CliError::InvalidInput(format!(
            "input folder does not exist: {}",
            input.display()
        )));
    }
    if !input.is_dir() {
        return Err(CliError::InvalidInput(format!(
            "input path is not a directory: {}",
            input.display()
        )));
    }
    // Permission check — attempt to read the directory (F-19)
    std::fs::read_dir(input).map_err(|e| {
        print_permission_help();
        CliError::InvalidInput(format!("cannot read input folder: {e}"))
    })?;

    // Resolve output directory via platform_paths (F-21)
    let output_dir = crate::paths::project_output_dir(name);

    // Interactive confirmation unless --yes (F-20)
    if !yes {
        eprintln!("Project: {name}");
        eprintln!("  Input:  {}", input.display());
        eprintln!("  Output: {}", output_dir.display());
        eprint!("Create? [y/N] ");
        let mut answer = String::new();
        if std::io::stdin().read_line(&mut answer).is_err() || !confirmed(&answer) {
            return Err(CliError::NotFound("Aborted.".into()));
        }
    }

    // Create output directory on local filesystem
    std::fs::create_dir_all(&output_dir).map_err(|e| {
        print_permission_help();
        CliError::Io(e)
    })?;

    // Canonicalize paths for storage
    let input_abs = std::fs::canonicalize(input).unwrap_or_else(|_| input.clone());
    let output_abs = std::fs::canonicalize(&output_dir).unwrap_or_else(|_| output_dir.clone());

    // Register project in daemon DB via HTTP API
    let body = serde_json::json!({
        "name": name,
        "path": input_abs.to_string_lossy(),
        "input_path": input_abs.to_string_lossy(),
        "output_path": output_abs.to_string_lossy(),
    });

    let client = reqwest::Client::new();
    let resp = client
        .post(format!("{api_url}/api/dashboard/projects"))
        .json(&body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;

    let status = resp.status();
    let val: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
    println!(
        "{}",
        serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
    );
    if !status.is_success() {
        return Err(CliError::NotFound("API returned non-success status".into()));
    }
    Ok(())
}

async fn handle_show(id: &str, api_url: &str) -> Result<(), CliError> {
    let project_url = format!("{api_url}/api/dashboard/projects");
    let resp = reqwest::get(&project_url)
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    let val: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;

    let project = val
        .as_array()
        .and_then(|arr| arr.iter().find(|p| p["id"].as_str() == Some(id)));
    match project {
        Some(p) => {
            let mut out = p.clone();
            let count = fetch_deliverable_count(id, api_url).await;
            out["deliverable_count"] = serde_json::json!(count);
            println!(
                "{}",
                serde_json::to_string_pretty(&out).unwrap_or_else(|_| out.to_string())
            );
            Ok(())
        }
        None => Err(CliError::NotFound(format!("project not found: {id}"))),
    }
}

async fn handle_plans(id: &str, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/project/{id}/tree");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to fetch project tree".into()))?;
    crate::cli_project_tree::print_project_tree(&val, id);
    Ok(())
}

async fn fetch_deliverable_count(project_id: &str, api_url: &str) -> i64 {
    let url = format!("{api_url}/api/deliverables?project_id={project_id}&count_only=true");
    match reqwest::get(&url).await {
        Ok(resp) => match resp.json::<serde_json::Value>().await {
            Ok(v) => v.get("count")
                .and_then(|c| c.as_i64())
                .or_else(|| v.as_array().map(|a| a.len() as i64))
                .unwrap_or(0),
            Err(_) => 0,
        },
        Err(_) => 0,
    }
}

fn confirmed(answer: &str) -> bool {
    matches!(answer.trim().to_lowercase().as_str(), "y" | "yes")
}

/// Print OS-specific instructions for permission errors (F-19)
fn print_permission_help() {
    if cfg!(target_os = "macos") {
        eprintln!(
            "hint: on macOS, grant Full Disk Access to your terminal app via\n  \
             System Settings → Privacy & Security → Full Disk Access"
        );
    } else if cfg!(target_os = "linux") {
        eprintln!(
            "hint: on Linux, check folder permissions with `ls -la` and fix with\n  \
             chmod -R u+rX <folder>"
        );
    } else {
        eprintln!("hint: ensure the current user has read permissions on the input folder");
    }
}
