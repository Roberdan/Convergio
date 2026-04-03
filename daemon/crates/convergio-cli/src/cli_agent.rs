// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Agent subcommands for the cvg CLI — delegates to daemon HTTP API via reqwest.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum AgentCommands {
    /// Transpile an agent from the catalog to a provider-specific format
    Transpile {
        /// Agent name (looked up via /api/agents/catalog)
        name: String,
        /// Target provider: claude-code, copilot-cli, generic-llm
        #[arg(long, default_value = "claude-code")]
        provider: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Start a new agent session
    Start {
        /// Agent name or type
        name: String,
        /// Task ID this agent is working on
        #[arg(long)]
        task_id: Option<i64>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Complete an active agent session
    Complete {
        /// Agent session ID
        agent_id: String,
        /// Completion summary
        #[arg(long)]
        summary: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List active agents
    List {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Sync agent catalog from .agent.md files in a directory
    Sync {
        /// Directory containing .agent.md files
        source_dir: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Enable an agent from catalog (write .agent.md to target dir)
    Enable {
        /// Agent name from catalog
        name: String,
        /// Directory to write the .agent.md file to
        #[arg(long)]
        target_dir: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Disable an agent (remove .agent.md from target dir)
    Disable {
        /// Agent name
        name: String,
        /// Directory containing the .agent.md file
        #[arg(long)]
        target_dir: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List agents in the catalog
    Catalog {
        /// Filter by category
        #[arg(long)]
        category: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Triage a problem — find the best agent for a given task
    Triage {
        /// Description of the problem to solve
        description: String,
        /// Optional domain filter (e.g. "technical", "core")
        #[arg(long)]
        domain: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show agent activity history (completed/failed sessions)
    History {
        /// ISO datetime lower bound (default: 7 days ago)
        #[arg(long)]
        since: Option<String>,
        /// ISO datetime upper bound
        #[arg(long)]
        until: Option<String>,
        /// Filter by status (completed, failed, running)
        #[arg(long)]
        status: Option<String>,
        /// Filter by model name
        #[arg(long)]
        model: Option<String>,
        /// Max rows (default 20, max 500)
        #[arg(long)]
        limit: Option<u32>,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Spawn an agent from the catalog with isolated workspace
    Spawn {
        /// Agent name from catalog
        name: String,
        /// Task ID to assign
        #[arg(long)]
        task: Option<i64>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a new agent in the catalog
    Create {
        /// Agent name
        name: String,
        /// Agent category
        #[arg(long, default_value = "")]
        category: String,
        /// Agent description
        #[arg(long, default_value = "")]
        description: String,
        /// Model to use
        #[arg(long, default_value = "claude-sonnet-4-6")]
        model: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

#[cfg(test)]
#[path = "cli_agent_tests.rs"]
mod tests;
