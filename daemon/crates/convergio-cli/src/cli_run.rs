// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Run subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum RunCommands {
    /// Create a new execution run
    Create {
        /// Plan ID to run
        plan_id: i64,
        /// Optional run label
        #[arg(long)]
        label: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List execution runs
    List {
        /// Filter by plan ID
        #[arg(long)]
        plan_id: Option<i64>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Pause a running execution
    Pause {
        /// Run ID to pause
        run_id: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Resume a paused execution
    Resume {
        /// Run ID to resume
        run_id: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: RunCommands) -> Result<(), CliError> {
    match cmd {
        RunCommands::Create {
            plan_id,
            label,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "plan_id": plan_id,
                "label": label,
            });
            post_and_print(&format!("{api_url}/api/runs"), &body, human).await
        }
        RunCommands::List {
            plan_id,
            human,
            api_url,
        } => {
            let url = match plan_id {
                Some(id) => format!("{api_url}/api/runs?plan_id={id}"),
                None => format!("{api_url}/api/runs"),
            };
            fetch_and_print(&url, human).await
        }
        RunCommands::Pause {
            run_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            post_and_print(&format!("{api_url}/api/runs/{run_id}/pause"), &body, human).await
        }
        RunCommands::Resume {
            run_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            post_and_print(&format!("{api_url}/api/runs/{run_id}/resume"), &body, human).await
        }
    }
}

async fn fetch_and_print(url: &str, human: bool) -> Result<(), CliError> {
    let resp = reqwest::get(url)
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    let status = resp.status();
    let val: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
    print_value(&val, human);
    if !status.is_success() {
        return Err(CliError::NotFound("API returned non-success status".into()));
    }
    Ok(())
}

async fn post_and_print(url: &str, body: &serde_json::Value, human: bool) -> Result<(), CliError> {
    let client = reqwest::Client::new();
    let resp = client
        .post(url)
        .json(body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    let status = resp.status();
    let val: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
    print_value(&val, human);
    if !status.is_success() {
        return Err(CliError::NotFound("API returned non-success status".into()));
    }
    Ok(())
}

fn print_value(val: &serde_json::Value, human: bool) {
    if human {
        println!(
            "{}",
            serde_json::to_string_pretty(val).unwrap_or_else(|_| val.to_string())
        );
    } else {
        println!("{val}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn run_commands_create_variant_exists() {
        let cmd = RunCommands::Create {
            plan_id: 685,
            label: Some("wave-1".to_string()),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, RunCommands::Create { plan_id: 685, .. }));
    }

    #[test]
    fn run_commands_list_variant_exists() {
        let cmd = RunCommands::List {
            plan_id: None,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, RunCommands::List { plan_id: None, .. }));
    }

    #[test]
    fn run_commands_pause_variant_exists() {
        let cmd = RunCommands::Pause {
            run_id: "run-42".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, RunCommands::Pause { .. }));
    }

    #[test]
    fn run_commands_resume_variant_exists() {
        let cmd = RunCommands::Resume {
            run_id: "run-42".to_string(),
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, RunCommands::Resume { .. }));
    }

    #[test]
    fn run_list_url_with_plan_filter() {
        let plan_id = Some(685i64);
        let api_url = "http://localhost:8420";
        let url = match plan_id {
            Some(id) => format!("{api_url}/api/runs?plan_id={id}"),
            None => format!("{api_url}/api/runs"),
        };
        assert!(url.contains("plan_id=685"));
    }

    #[test]
    fn run_pause_url_format() {
        let run_id = "run-99";
        let url = format!("http://localhost:8420/api/runs/{run_id}/pause");
        assert_eq!(url, "http://localhost:8420/api/runs/run-99/pause");
    }
}
