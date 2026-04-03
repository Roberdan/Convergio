// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Checkpoint subcommand — save/restore plan state via daemon HTTP API.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum CheckpointCommands {
    /// Save current plan state to checkpoint file
    Save {
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Restore plan state from checkpoint file
    Restore {
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: CheckpointCommands) {
    match cmd {
        CheckpointCommands::Save {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({ "plan_id": plan_id });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/checkpoint/save"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        CheckpointCommands::Restore {
            plan_id,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/checkpoint/restore?plan_id={plan_id}"),
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
mod tests {
    use super::*;

    #[test]
    fn checkpoint_save_variant_exists() {
        let cmd = CheckpointCommands::Save {
            plan_id: 685,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, CheckpointCommands::Save { plan_id: 685, .. }));
    }

    #[test]
    fn checkpoint_restore_variant_exists() {
        let cmd = CheckpointCommands::Restore {
            plan_id: 42,
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(
            cmd,
            CheckpointCommands::Restore { plan_id: 42, .. }
        ));
    }

    #[test]
    fn checkpoint_save_body_shape() {
        let body = serde_json::json!({ "plan_id": 685_i64 });
        assert_eq!(body["plan_id"], 685);
    }
}
