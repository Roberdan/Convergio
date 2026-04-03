use clap::Parser;
use convergio_cli::cli_commands::Commands;
use std::env;
use std::process::ExitCode;

#[derive(Debug, Parser)]
#[command(
    name = "cvg",
    version,
    about = "Convergio Platform CLI — orchestrate agents, plans, and infrastructure",
    long_about = "Convergio Platform CLI — pure HTTP client.\n\n\
        Quick start:\n  cvg status              # Platform overview\n  \
        cvg plan list             # List execution plans\n  \
        cvg who agents            # See active agents\n  \
        cvg org list              # List organizations\n  \
        cvg cheatsheet            # Full command reference"
)]
struct Cli {
    #[arg(long, default_value_t = false)]
    version_json: bool,
    #[command(subcommand)]
    command: Option<Commands>,
}

#[tokio::main]
async fn main() -> ExitCode {
    // Load ~/.convergio/env for auth tokens
    let env_path = convergio_cli::paths::convergio_dir().join("env");
    if let Ok(contents) = std::fs::read_to_string(&env_path) {
        for line in contents.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if let Some((k, v)) = line.split_once('=') {
                if env::var(k.trim()).is_err() {
                    env::set_var(k.trim(), v.trim());
                }
            }
        }
    }

    let cli = Cli::parse();

    if cli.version_json {
        let payload = serde_json::json!({
            "binary": "cvg",
            "version": env!("CARGO_PKG_VERSION")
        });
        println!("{payload}");
        return ExitCode::SUCCESS;
    }

    // First-run hint
    if let Some(ref command) = cli.command {
        if !matches!(command, Commands::Setup { .. })
            && !convergio_cli::paths::config_path().exists()
        {
            eprintln!("hint: First time? Run `cvg setup` to configure Convergio.");
        }
    }

    if let Some(command) = cli.command {
        return convergio_cli::dispatch::dispatch(command).await;
    }

    println!("cvg — Convergio Platform CLI. Use --help for commands.");
    ExitCode::SUCCESS
}
