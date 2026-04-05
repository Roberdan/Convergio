// Self-build CLI subcommands — triggers daemon self-build via HTTP API.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum BuildCommands {
    /// Trigger a self-build (check + test + release build)
    #[command(name = "self")]
    Trigger {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Check build status by ID
    Status {
        /// Build ID to check
        build_id: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List recent builds
    History {
        /// Max number of builds to show
        #[arg(long, default_value = "20")]
        limit: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Deploy a successful build (binary swap + restart)
    Deploy {
        /// Build ID to deploy
        build_id: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Rollback to previous binary
    Rollback {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: BuildCommands) -> Result<(), CliError> {
    match cmd {
        BuildCommands::Trigger { human, api_url } => {
            let body = serde_json::json!({});
            post_and_print(&format!("{api_url}/api/build/self"), &body, human).await
        }
        BuildCommands::Status {
            build_id,
            human,
            api_url,
        } => fetch_and_print(&format!("{api_url}/api/build/status/{build_id}"), human).await,
        BuildCommands::History {
            limit,
            human,
            api_url,
        } => fetch_and_print(&format!("{api_url}/api/build/history?limit={limit}"), human).await,
        BuildCommands::Deploy {
            build_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            post_and_print(
                &format!("{api_url}/api/build/deploy/{build_id}"),
                &body,
                human,
            )
            .await
        }
        BuildCommands::Rollback { human, api_url } => {
            let body = serde_json::json!({});
            post_and_print(&format!("{api_url}/api/build/rollback"), &body, human).await
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
    fn build_trigger_variant_exists() {
        let cmd = BuildCommands::Trigger {
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BuildCommands::Trigger { .. }));
    }

    #[test]
    fn build_status_variant_exists() {
        let cmd = BuildCommands::Status {
            build_id: "abc-123".to_string(),
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BuildCommands::Status { .. }));
    }

    #[test]
    fn build_deploy_variant_exists() {
        let cmd = BuildCommands::Deploy {
            build_id: "abc-123".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BuildCommands::Deploy { .. }));
    }

    #[test]
    fn build_history_url_format() {
        let api_url = "http://localhost:8420";
        let limit = 10;
        let url = format!("{api_url}/api/build/history?limit={limit}");
        assert_eq!(url, "http://localhost:8420/api/build/history?limit=10");
    }
}
