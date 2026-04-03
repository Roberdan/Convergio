// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Plan subcommands for cvg CLI — daemon HTTP API. Handlers in cli_plan_handlers.rs.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum PlanCommands {
    /// List plans (all by default, newest first)
    List {
        /// Filter by status: done, doing, todo, cancelled, active
        #[arg(long)]
        status: Option<String>,
        /// Max plans to show (default 20, 0 = unlimited)
        #[arg(long)]
        limit: Option<i64>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show execution tree for a plan
    #[command(alias = "execution-tree")]
    Tree {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show plan JSON
    Show {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Check plan staleness (drift check)
    Drift {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Validate a wave in a plan (Thor)
    Validate {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a new plan
    Create {
        /// Project identifier
        project_id: String,
        /// Plan name
        name: String,
        /// Source spec file path
        #[arg(long)]
        source_file: Option<String>,
        /// Parent plan ID (makes this a sub-plan, promotes parent to master)
        #[arg(long)]
        parent: Option<i64>,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Import a spec YAML into a plan
    Import {
        /// Plan ID to import into
        plan_id: i64,
        /// Path to spec YAML file
        spec_file: String,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Start plan execution
    Start {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Mark plan as complete
    Complete {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Cancel a plan with reason
    Cancel {
        /// Plan ID
        plan_id: i64,
        /// Cancellation reason
        reason: String,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Approve a plan for execution
    Approve {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Check plan readiness (review, tasks, models)
    Readiness {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Print example spec YAML template with all supported fields
    Template,
    /// Close a plan — triggers completion + mesh broadcast
    Close {
        /// Plan ID
        plan_id: i64,
        #[arg(long)]
        human: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: PlanCommands) -> Result<(), crate::cli_error::CliError> {
    crate::cli_plan_handlers::dispatch(cmd).await
}

#[cfg(test)]
#[path = "cli_plan_tests.rs"]
mod tests;
