// NOTE: Watchdog monitoring (previously partly overlapping with voice pipeline)
// has been superseded by the kernel module. Use `cvg kernel` for health monitoring.
// This module remains for voice pipeline management (start/stop/status/test).
use crate::cli_error::CliError;
use clap::Subcommand;

const DEFAULT_API: &str = "http://127.0.0.1:8420";

#[derive(Debug, Subcommand)]
pub enum VoiceCommands {
    /// Start voice listening (cvg voice start)
    Start {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Stop voice listening (cvg voice stop)
    Stop {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Show voice pipeline status (cvg voice status)
    Status {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        #[arg(long)]
        human: bool,
    },
    /// Test audio setup (cvg voice test)
    Test {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
}

/// Dispatch voice pipeline commands.
///
/// Health monitoring previously accessible via related watchdog commands is now
/// available through `cvg kernel`. This handler is for voice pipeline only.
pub async fn handle(cmd: VoiceCommands) -> Result<(), CliError> {
    // Deprecation notice: watchdog monitoring moved to `cvg kernel`.
    // Voice pipeline management (start/stop/status/test) continues here.
    match cmd {
        VoiceCommands::Start { api_url } => {
            let body = serde_json::json!({});
            let url = format!("{api_url}/api/voice/start");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        VoiceCommands::Stop { api_url } => {
            let body = serde_json::json!({});
            let url = format!("{api_url}/api/voice/stop");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        VoiceCommands::Status { api_url, human } => {
            crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/voice/status"),
                human,
            ).await
        }
        VoiceCommands::Test { api_url } => {
            let body = serde_json::json!({});
            let url = format!("{api_url}/api/voice/test");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
    }
}
