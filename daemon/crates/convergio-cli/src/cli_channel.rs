// Channel CLI subcommands: list, status, test, send.
// Delegates to daemon HTTP API at /api/channels.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum ChannelCommands {
    /// List all registered channels and connection status
    List {
        /// Output as JSON (default: pretty table)
        #[arg(long)]
        json: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show verbose health status for all channels
    Status {
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Send a test message through a channel and verify delivery
    Test {
        /// Channel name (e.g. ntfy, telegram)
        name: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Send a message through a specific channel
    Send {
        /// Channel name (e.g. ntfy, telegram)
        name: String,
        /// Message text to send
        message: String,
        /// Severity level: info, warning, error, critical
        #[arg(long, default_value = "info")]
        severity: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: ChannelCommands) -> Result<(), CliError> {
    match cmd {
        ChannelCommands::List { json, api_url } => handle_list(json, &api_url).await,
        ChannelCommands::Status { api_url } => handle_status(&api_url).await,
        ChannelCommands::Test { name, api_url } => handle_test(&name, &api_url).await,
        ChannelCommands::Send {
            name,
            message,
            severity,
            api_url,
        } => handle_send(&name, &message, &severity, &api_url).await,
    }
}

async fn handle_list(as_json: bool, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/channels");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to list channels".into()))?;

    if as_json {
        println!(
            "{}",
            serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
        );
        return Ok(());
    }

    let channels = val["channels"].as_array().cloned().unwrap_or_default();
    if channels.is_empty() {
        println!("No channels registered.");
        return Ok(());
    }
    println!("{:<20} {:<12} {:<12}", "CHANNEL", "CONNECTED", "ERRORS");
    println!("{}", "-".repeat(50));
    for ch in &channels {
        let name = ch["name"].as_str().unwrap_or("-");
        let connected = ch["connected"].as_bool().unwrap_or(false);
        let errors = ch["error_count"].as_u64().unwrap_or(0);
        let status = if connected { "yes" } else { "no" };
        println!("{:<20} {:<12} {:<12}", name, status, errors);
    }
    Ok(())
}

async fn handle_status(api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/channels");
    let val = crate::cli_http::get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("failed to get channel status".into()))?;

    let channels = val["channels"].as_array().cloned().unwrap_or_default();
    if channels.is_empty() {
        println!("No channels registered.");
        return Ok(());
    }

    for ch in &channels {
        let name = ch["name"].as_str().unwrap_or("-");
        let connected = ch["connected"].as_bool().unwrap_or(false);
        let errors = ch["error_count"].as_u64().unwrap_or(0);
        let last_msg = ch["last_message_at"].as_str().unwrap_or("never");
        println!("--- {} ---", name);
        println!("  Connected:    {}", if connected { "yes" } else { "no" });
        println!("  Errors:       {errors}");
        println!("  Last message: {last_msg}");
        println!();
    }
    Ok(())
}

async fn handle_test(name: &str, api_url: &str) -> Result<(), CliError> {
    let payload = serde_json::json!({
        "message": "Convergio channel test message",
        "severity": "info"
    });
    let url = format!("{api_url}/api/channels/{name}/send");
    let val = crate::cli_http::post_and_return(&url, &payload)
        .await
        .map_err(|_| CliError::ApiCallFailed(format!("failed to test channel '{name}'")))?;

    let delivered = val["delivered"].as_bool().unwrap_or(false);
    if delivered {
        println!("Channel '{name}' test: DELIVERED");
    } else {
        println!("Channel '{name}' test: NOT DELIVERED (check channel config)");
    }
    Ok(())
}

async fn handle_send(
    name: &str,
    message: &str,
    severity: &str,
    api_url: &str,
) -> Result<(), CliError> {
    let payload = serde_json::json!({
        "message": message,
        "severity": severity,
    });
    let url = format!("{api_url}/api/channels/{name}/send");
    crate::cli_http::post_and_print(&url, &payload, true)
        .await
        .map_err(|_| CliError::ApiCallFailed(format!("failed to send to channel '{name}'")))
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[derive(Debug, Parser)]
    struct TestCli {
        #[command(subcommand)]
        cmd: ChannelCommands,
    }

    #[test]
    fn parse_channel_list() {
        let cli = TestCli::parse_from(["test", "list"]);
        assert!(matches!(cli.cmd, ChannelCommands::List { json: false, .. }));
    }

    #[test]
    fn parse_channel_list_json() {
        let cli = TestCli::parse_from(["test", "list", "--json"]);
        assert!(matches!(cli.cmd, ChannelCommands::List { json: true, .. }));
    }

    #[test]
    fn parse_channel_status() {
        let cli = TestCli::parse_from(["test", "status"]);
        assert!(matches!(cli.cmd, ChannelCommands::Status { .. }));
    }

    #[test]
    fn parse_channel_test() {
        let cli = TestCli::parse_from(["test", "test", "ntfy"]);
        if let ChannelCommands::Test { name, .. } = cli.cmd {
            assert_eq!(name, "ntfy");
        } else {
            panic!("expected Test variant");
        }
    }

    #[test]
    fn parse_channel_send() {
        let cli = TestCli::parse_from(["test", "send", "ntfy", "Hello world"]);
        if let ChannelCommands::Send {
            name,
            message,
            severity,
            ..
        } = cli.cmd
        {
            assert_eq!(name, "ntfy");
            assert_eq!(message, "Hello world");
            assert_eq!(severity, "info");
        } else {
            panic!("expected Send variant");
        }
    }

    #[test]
    fn parse_channel_send_with_severity() {
        let cli = TestCli::parse_from([
            "test",
            "send",
            "telegram",
            "Alert!",
            "--severity",
            "critical",
        ]);
        if let ChannelCommands::Send { name, severity, .. } = cli.cmd {
            assert_eq!(name, "telegram");
            assert_eq!(severity, "critical");
        } else {
            panic!("expected Send variant");
        }
    }
}
