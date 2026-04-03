// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Task subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

// Re-export for tests that use `super::*`
#[cfg(test)]
pub use crate::cli_task_format::print_mechanical_human;

#[derive(Debug, Subcommand)]
pub enum TaskCommands {
    /// Update a task status
    Update {
        /// Task DB ID
        task_id: i64,
        /// New status (e.g. in_progress, done, blocked)
        status: String,
        /// Optional summary message
        #[arg(long)]
        summary: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Validate a task (Thor gate)
    Validate {
        /// Task DB ID
        task_id: i64,
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Search the knowledge base
    KbSearch {
        /// Search query
        query: String,
        /// Maximum results to return
        #[arg(long, default_value_t = 5)]
        limit: u32,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a new task in an existing plan/wave
    Create {
        /// Plan DB ID
        plan_id: i64,
        /// Wave DB ID (wave_id_fk)
        wave_db_id: i64,
        /// Task string identifier (e.g. T1-01)
        task_id: String,
        /// Task title
        title: String,
        /// Priority (default: P2)
        #[arg(long, default_value = "P2")]
        priority: String,
        /// Task type (default: feature)
        #[arg(long = "type", default_value = "feature")]
        task_type: String,
        /// Model override
        #[arg(long, default_value = "")]
        model: String,
        /// Task description
        #[arg(long, default_value = "")]
        description: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Approve the deliverable linked to a task
    Approve {
        /// Task DB ID
        task_id: i64,
        /// Approver name or comment
        #[arg(long)]
        comment: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: TaskCommands) -> Result<(), crate::cli_error::CliError> {
    match cmd {
        TaskCommands::Update {
            task_id,
            status,
            summary,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "task_id": task_id,
                "status": status,
                "summary": summary,
            });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/task/update"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        TaskCommands::Validate {
            task_id,
            plan_id,
            human,
            api_url,
        } => {
            let url = format!("{api_url}/api/plan-db/validate-task/{task_id}/{plan_id}");
            let resp = reqwest::get(&url).await.map_err(|e| {
                crate::cli_error::CliError::ApiCallFailed(format!(
                    "error connecting to daemon: {e}"
                ))
            })?;
            let val: serde_json::Value = resp.json().await.map_err(|e| {
                crate::cli_error::CliError::ApiCallFailed(format!("error parsing response: {e}"))
            })?;
            if human {
                crate::cli_task_format::print_mechanical_human(&val);
            } else {
                println!("{val}");
            }
            // Return error if mechanical gates rejected
            let rejected = val
                .get("mechanical")
                .and_then(|m| m.get("status"))
                .and_then(serde_json::Value::as_str)
                == Some("REJECTED");
            if rejected {
                return Err(crate::cli_error::CliError::ValidationRejected(
                    "mechanical gates rejected".into(),
                ));
            }
        }
        TaskCommands::KbSearch {
            query,
            limit,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/kb-search?q={query}&limit={limit}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        TaskCommands::Create {
            plan_id,
            wave_db_id,
            task_id,
            title,
            priority,
            task_type,
            model,
            description,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "plan_id": plan_id,
                "wave_id_fk": wave_db_id,
                "task_id": task_id,
                "title": title,
                "priority": priority,
                "type": task_type,
                "model": model,
                "description": description,
            });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/task/create"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        TaskCommands::Approve {
            task_id,
            comment,
            human,
            api_url,
        } => {
            crate::cli_task_approve::handle(task_id, comment, human, &api_url).await?;
        }
    }
    Ok(())
}

#[cfg(test)]
#[path = "cli_task_tests.rs"]
mod tests;
