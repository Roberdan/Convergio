// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// `cvg reap [--dry-run]` — delegates reaping to daemon HTTP API.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum ReapCommands {
    /// Run all reapers (worktree, branch, lock-file). Add --dry-run to preview only.
    Run {
        /// Preview changes without removing anything.
        #[arg(long)]
        dry_run: bool,
        /// Repository root (default: current directory).
        #[arg(long, default_value = ".")]
        repo_root: String,
        /// Lock-file directory (default: /tmp).
        #[arg(long, default_value = "/tmp")]
        lock_dir: String,
        /// Human-readable output (default: JSON).
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: ReapCommands) {
    match cmd {
        ReapCommands::Run {
            dry_run,
            repo_root,
            lock_dir,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "dry_run": dry_run,
                "repo_root": repo_root,
                "lock_dir": lock_dir,
            });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/reap/run"),
                &body,
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
    fn reap_run_command_dry_run_field() {
        let cmd = ReapCommands::Run {
            dry_run: true,
            repo_root: ".".into(),
            lock_dir: "/tmp".into(),
            human: false,
            api_url: "http://localhost:8420".into(),
        };
        assert!(matches!(cmd, ReapCommands::Run { dry_run: true, .. }));
    }

    #[test]
    fn reap_run_command_default_dirs() {
        let cmd = ReapCommands::Run {
            dry_run: false,
            repo_root: ".".into(),
            lock_dir: "/tmp".into(),
            human: true,
            api_url: "http://localhost:8420".into(),
        };
        assert!(matches!(cmd, ReapCommands::Run { human: true, .. }));
    }
}
