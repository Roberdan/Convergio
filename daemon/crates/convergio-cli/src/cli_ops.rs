// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Mesh and Session subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum MeshCommands {
    /// Send a heartbeat to the mesh (POST /api/heartbeat)
    Heartbeat {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show current mesh status (GET /api/mesh)
    Status {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show cluster-level heartbeat status (GET /api/heartbeat/status)
    ClusterStatus {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Join a mesh by registering with a coordinator node
    Join {
        /// Coordinator daemon URL (e.g. http://100.89.245.79:8420)
        coordinator_url: String,
    },
}

#[derive(Debug, Subcommand)]
pub enum SessionCommands {
    /// Clean up old/stale sessions
    Reap {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Trigger session recovery
    Recovery {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Check session / dashboard health (GET /api/dashboard)
    Check {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

#[derive(Debug, Subcommand)]
pub enum MetricsCommands {
    /// Show metrics summary (GET /api/metrics/summary)
    Summary {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Trigger metrics collection (POST /api/metrics/collect)
    Collect {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

#[derive(Debug, Subcommand)]
pub enum AlertCommands {
    /// List active notifications (GET /api/notifications)
    List {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle_mesh(cmd: MeshCommands) {
    match cmd {
        MeshCommands::Heartbeat { human, api_url } => {
            // POST with empty body — signals this node is alive
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/heartbeat"),
                &serde_json::json!({}),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        MeshCommands::Status { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/mesh"), human).await
            {
                eprintln!("error: {e}");
            }
        }
        MeshCommands::ClusterStatus { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/heartbeat/status"), human)
                    .await
            {
                eprintln!("error: {e}");
            }
        }
        MeshCommands::Join { coordinator_url } => {
            if let Err(e) = crate::cli_mesh_join::handle_mesh_join(&coordinator_url).await {
                eprintln!("error: {e}");
            }
        }
    }
}

pub async fn handle_session(cmd: SessionCommands) {
    match cmd {
        SessionCommands::Reap { human, api_url } => {
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/sessions/reap"),
                &serde_json::json!({}),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        SessionCommands::Recovery { human, api_url } => {
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/sessions/recovery"),
                &serde_json::json!({}),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        SessionCommands::Check { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/dashboard"), human).await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

pub async fn handle_metrics(cmd: MetricsCommands) {
    match cmd {
        MetricsCommands::Summary { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/metrics/summary"), human)
                    .await
            {
                eprintln!("error: {e}");
            }
        }
        MetricsCommands::Collect { human, api_url } => {
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/metrics/collect"),
                &serde_json::json!({}),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

pub async fn handle_alert(cmd: AlertCommands) {
    match cmd {
        AlertCommands::List { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/notifications"), human)
                    .await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

#[cfg(test)]
#[path = "cli_ops_tests.rs"]
mod tests;
