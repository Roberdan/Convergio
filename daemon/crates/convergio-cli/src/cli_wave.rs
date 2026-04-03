// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Wave subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.
// Handler implementations live in cli_wave_handlers.rs (250-line split).

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum WaveCommands {
    /// Update wave status
    Update {
        /// Wave DB ID
        wave_id: i64,
        /// New status (e.g. in_progress, done, blocked)
        status: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show context for a plan (waves + tasks summary)
    Context {
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a new wave for a plan (also provisions a workspace)
    Create {
        /// Plan ID
        plan_id: i64,
        /// Wave ID (human-readable, e.g. W1, W2)
        wave_id: String,
        /// Wave name/description
        name: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Merge a completed wave via the workspace release pipeline
    Merge {
        /// Plan ID
        plan_id: i64,
        /// Wave DB ID
        wave_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Validate a wave: quality gates first, then Thor (Opus, wave-level)
    Validate {
        /// Wave DB ID
        wave_id: i64,
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Release a wave workspace (alias for workspace release pipeline)
    Release {
        /// Wave DB ID
        wave_id: i64,
        /// Plan ID
        plan_id: i64,
        /// GitHub repo slug (owner/repo)
        #[arg(long)]
        repo: String,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: WaveCommands) -> Result<(), CliError> {
    match cmd {
        WaveCommands::Update {
            wave_id,
            status,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "wave_id": wave_id,
                "status": status,
            });
            crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/wave/update"),
                &body,
                human,
            )
            .await?;
        }
        WaveCommands::Context {
            plan_id,
            human,
            api_url,
        } => {
            crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/context/{plan_id}"),
                human,
            )
            .await?;
        }
        WaveCommands::Create {
            plan_id,
            wave_id,
            name,
            human,
            api_url,
        } => {
            crate::cli_wave_handlers::handle_create(plan_id, wave_id, name, human, api_url).await?;
        }
        WaveCommands::Merge {
            plan_id,
            wave_id,
            human,
            api_url,
        } => {
            crate::cli_wave_handlers::handle_merge(plan_id, wave_id, human, api_url).await?;
        }
        WaveCommands::Validate {
            wave_id,
            plan_id,
            human,
            api_url,
        } => {
            crate::cli_wave_handlers::handle_validate(wave_id, plan_id, human, api_url).await?;
        }
        WaveCommands::Release {
            wave_id,
            plan_id,
            repo,
            human,
            api_url,
        } => {
            crate::cli_wave_handlers::handle_release(wave_id, plan_id, repo, human, api_url)
                .await?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wave_commands_update_variant_exists() {
        let cmd = WaveCommands::Update {
            wave_id: 1,
            status: "done".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, WaveCommands::Update { wave_id: 1, .. }));
    }

    #[test]
    fn wave_commands_context_variant_exists() {
        let cmd = WaveCommands::Context {
            plan_id: 685,
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, WaveCommands::Context { plan_id: 685, .. }));
    }

    #[test]
    fn wave_commands_validate_variant_exists() {
        let cmd = WaveCommands::Validate {
            wave_id: 3,
            plan_id: 685,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, WaveCommands::Validate { wave_id: 3, .. }));
    }

    #[test]
    fn wave_commands_create_variant_exists() {
        let cmd = WaveCommands::Create {
            plan_id: 687,
            wave_id: "W1".to_string(),
            name: "Foundation".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, WaveCommands::Create { plan_id: 687, .. }));
    }

    #[test]
    fn wave_commands_merge_variant_exists() {
        let cmd = WaveCommands::Merge {
            plan_id: 687,
            wave_id: 2088,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, WaveCommands::Merge { wave_id: 2088, .. }));
    }

    #[test]
    fn wave_commands_release_variant_exists() {
        let cmd = WaveCommands::Release {
            wave_id: 42,
            plan_id: 698,
            repo: "org/convergio".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(
            cmd,
            WaveCommands::Release {
                wave_id: 42,
                plan_id: 698,
                ..
            }
        ));
    }

    #[test]
    fn wave_update_body_shape() {
        let body = serde_json::json!({
            "wave_id": 2_i64,
            "status": "in_progress",
        });
        assert_eq!(body["wave_id"], 2);
        assert_eq!(body["status"], "in_progress");
    }
}
