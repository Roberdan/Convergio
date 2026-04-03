// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Workspace subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum WorkspaceCommands {
    /// Create a plan/wave workspace
    Create {
        /// Plan ID
        #[arg(long)]
        plan: Option<i64>,
        /// Wave DB ID
        #[arg(long)]
        wave: Option<i64>,
        /// Human-readable output
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a feature branch workspace
    CreateFeature {
        /// Branch name
        branch: String,
        /// Human-readable output
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Delete a workspace
    Delete {
        /// Workspace ID
        workspace_id: String,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List workspaces
    List {
        /// Filter by plan ID
        #[arg(long)]
        plan: Option<i64>,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show workspace status
    Status {
        /// Workspace ID
        workspace_id: String,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show workspace events
    Events {
        /// Workspace ID
        workspace_id: String,
        /// Max events to return
        #[arg(long, default_value = "20")]
        limit: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: WorkspaceCommands) {
    match cmd {
        WorkspaceCommands::Create {
            plan,
            wave,
            human,
            api_url,
        } => {
            let body = serde_json::json!({"plan_id": plan, "wave_db_id": wave});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/workspace/create"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        WorkspaceCommands::CreateFeature {
            branch,
            human,
            api_url,
        } => {
            let body = serde_json::json!({"feature": true, "branch": branch});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/workspace/create"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        WorkspaceCommands::Delete {
            workspace_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({"workspace_id": workspace_id});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/workspace/delete"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        WorkspaceCommands::List {
            plan,
            human,
            api_url,
        } => {
            let url = if let Some(pid) = plan {
                format!("{api_url}/api/workspace/list?plan_id={pid}")
            } else {
                format!("{api_url}/api/workspace/list")
            };
            if let Err(e) = crate::cli_http::fetch_and_print(&url, human).await {
                eprintln!("error: {e}");
            }
        }
        WorkspaceCommands::Status {
            workspace_id,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/workspace/status/{workspace_id}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        WorkspaceCommands::Events {
            workspace_id,
            limit,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!(
                    "{api_url}/api/workspace/events?workspace_id={workspace_id}&limit={limit}"
                ),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

#[cfg(test)]
#[path = "cli_workspace_tests.rs"]
mod tests;
