// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// CLI commands for the kernel health monitor (cvg kernel start/stop/status/logs/test/here/say).

use crate::cli_error::CliError;
use clap::Subcommand;

const DEFAULT_API: &str = "http://localhost:8420";

#[derive(Debug, Subcommand)]
pub enum KernelCommands {
    /// Start the kernel engine (loads models, begins monitor loop)
    Start {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        /// Override MLX model to load
        #[arg(long)]
        model: Option<String>,
    },
    /// Stop the kernel engine (unloads models, stops monitor loop)
    Stop {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Show kernel status as table
    Status {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Query kernel_events (cvg kernel logs [--level WARN] [--limit 50])
    Logs {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        /// Minimum log level filter (DEBUG|INFO|WARN|ERROR)
        #[arg(long)]
        level: Option<String>,
        /// Maximum number of events to return
        #[arg(long, default_value_t = 50)]
        limit: u32,
    },
    /// Run all monitor checks once and report results
    Test {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Set this node as the active audio target (POST /api/kernel/active-node)
    Here {
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        /// Override node hostname (defaults to system hostname)
        #[arg(long)]
        node: Option<String>,
    },
    /// Debug TTS: speak text on the active node (stub — POST /api/kernel/speak)
    Say {
        /// Text to synthesise
        text: String,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        /// BCP-47 locale for TTS
        #[arg(long, default_value = "it-IT")]
        locale: String,
    },
    /// Download all MLX models required by the kernel (runs scripts/kernel/setup-models.sh)
    Setup {
        /// Path to setup-models.sh; defaults to scripts/kernel/setup-models.sh relative to cwd
        #[arg(long)]
        script: Option<String>,
    },
}

/// Dispatch kernel subcommands. Returns an exit code (0 = success).
pub async fn dispatch(cmd: KernelCommands) -> std::process::ExitCode {
    let result = dispatch_inner(cmd).await;
    match result {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            std::process::ExitCode::FAILURE
        }
    }
}

async fn dispatch_inner(cmd: KernelCommands) -> Result<(), CliError> {
    match cmd {
        KernelCommands::Status { api_url } => {
            let val = crate::cli_http::get_and_return(&format!("{api_url}/api/kernel/status"))
                .await
                .map_err(|code| CliError::ApiCallFailed(format!("exit {code}")))?;
            print_status_table(&val);
            Ok(())
        }
        KernelCommands::Start { api_url, model } => {
            let mut body = serde_json::json!({});
            if let Some(m) = model {
                body["model"] = serde_json::Value::String(m);
            }
            crate::cli_http::post_and_print(&format!("{api_url}/api/kernel/start"), &body, false)
                .await
        }
        KernelCommands::Stop { api_url } => {
            let body = serde_json::json!({});
            crate::cli_http::post_and_print(&format!("{api_url}/api/kernel/stop"), &body, false)
                .await
        }
        KernelCommands::Logs {
            api_url,
            level,
            limit,
        } => {
            let mut url = format!("{api_url}/api/kernel/logs?limit={limit}");
            if let Some(l) = level {
                url.push_str(&format!("&level={l}"));
            }
            let val = crate::cli_http::get_and_return(&url)
                .await
                .map_err(|code| CliError::ApiCallFailed(format!("exit {code}")))?;
            print_logs_table(&val);
            Ok(())
        }
        KernelCommands::Test { api_url } => {
            let body = serde_json::json!({});
            let val =
                crate::cli_http::post_and_return(&format!("{api_url}/api/kernel/test"), &body)
                    .await
                    .map_err(|code| CliError::ApiCallFailed(format!("exit {code}")))?;
            print_test_table(&val);
            Ok(())
        }
        KernelCommands::Here { api_url, node } => {
            let hostname = node.unwrap_or_else(|| {
                hostname::get()
                    .map(|h| h.into_string().unwrap_or_else(|_| "unknown".to_string()))
                    .unwrap_or_else(|e| {
                        eprintln!("warn: could not resolve hostname: {e}");
                        "unknown".to_string()
                    })
            });
            let body = serde_json::json!({ "node": hostname });
            crate::cli_http::post_and_print(
                &format!("{api_url}/api/kernel/active-node"),
                &body,
                false,
            )
            .await
        }
        KernelCommands::Say { text, api_url, locale } => {
            let body = serde_json::json!({ "text": text, "locale": locale });
            crate::cli_http::post_and_print(&format!("{api_url}/api/kernel/speak"), &body, false)
                .await
        }
        KernelCommands::Setup { script } => {
            let script_path = script.unwrap_or_else(|| {
                "scripts/kernel/setup-models.sh".to_string()
            });
            let status = std::process::Command::new("bash")
                .arg(&script_path)
                .status()
                .map_err(|e| CliError::ApiCallFailed(format!("failed to launch {script_path}: {e}")))?;
            if status.success() {
                Ok(())
            } else {
                Err(CliError::ApiCallFailed(format!(
                    "setup-models.sh exited with status {status}"
                )))
            }
        }
    }
}

/// Render GET /api/kernel/status as a two-column table.
fn print_status_table(val: &serde_json::Value) {
    let rows = [
        ("models_loaded", val["models_loaded"].to_string()),
        (
            "ram_gb",
            val["ram_gb"]
                .as_f64()
                .map(|f| format!("{f:.2}"))
                .unwrap_or_else(|| val["ram_gb"].to_string()),
        ),
        ("uptime_secs", val["uptime_secs"].to_string()),
        (
            "active_node",
            val["active_node"]
                .as_str()
                .unwrap_or("—")
                .to_string(),
        ),
        (
            "last_check",
            val["last_check"].as_str().unwrap_or("—").to_string(),
        ),
    ];
    println!("{:<16} {}", "field", "value");
    println!("{}", "-".repeat(40));
    for (k, v) in &rows {
        println!("{k:<16} {v}");
    }
}

/// Render GET /api/kernel/logs as a table.
fn print_logs_table(val: &serde_json::Value) {
    let empty = vec![];
    let events = val.as_array().unwrap_or(&empty);
    if events.is_empty() {
        println!("(no events)");
        return;
    }
    println!("{:<24} {:<8} {}", "timestamp", "level", "message");
    println!("{}", "-".repeat(72));
    for ev in events {
        let ts = ev["timestamp"].as_str().unwrap_or("?");
        let level = ev["level"].as_str().unwrap_or("?");
        let msg = ev["message"].as_str().unwrap_or("?");
        println!("{ts:<24} {level:<8} {msg}");
    }
}

/// Render POST /api/kernel/test results as a table.
fn print_test_table(val: &serde_json::Value) {
    let empty = vec![];
    let checks = val["checks"].as_array().unwrap_or(&empty);
    if checks.is_empty() {
        // Fall back to raw JSON if shape is unexpected.
        println!(
            "{}",
            serde_json::to_string_pretty(val).unwrap_or_else(|_| val.to_string())
        );
        return;
    }
    println!("{:<28} {:<8} {}", "check", "status", "detail");
    println!("{}", "-".repeat(72));
    for ch in checks {
        let name = ch["name"].as_str().unwrap_or("?");
        let status = ch["status"].as_str().unwrap_or("?");
        let detail = ch["detail"].as_str().unwrap_or("");
        println!("{name:<28} {status:<8} {detail}");
    }
}
