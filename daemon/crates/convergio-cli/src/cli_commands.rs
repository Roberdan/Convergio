// CLI Commands enum — all top-level subcommands for cvg.
// Pure HTTP client: server-side commands (Serve, Db, Hook, Daemon, Ipc, Tui)
// are NOT included here — they live in the daemon binary.

use crate::{
    cli_agent, cli_build, cli_bus, cli_capability, cli_channel, cli_checkpoint, cli_delegation,
    cli_domain, cli_kb, cli_kernel, cli_lock, cli_memory, cli_ops, cli_org, cli_plan, cli_project,
    cli_reap, cli_repo, cli_review, cli_run, cli_skill, cli_task, cli_voice, cli_wave, cli_who,
    cli_workspace,
};
use clap::Subcommand;
use std::path::PathBuf;

#[derive(Debug, Subcommand)]
pub enum Commands {
    #[command(
        next_help_heading = "User Commands",
        about = "Initialize Convergio on this machine"
    )]
    Setup {
        #[arg(long)]
        defaults: bool,
    },
    #[command(about = "Show platform status, active plans, and recent activity")]
    Status {
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    #[command(about = "Manage execution plans (create, list, validate, complete)")]
    Plan {
        #[command(subcommand)]
        command: cli_plan::PlanCommands,
    },
    #[command(about = "Manage projects and repositories")]
    Project {
        #[command(subcommand)]
        command: cli_project::ProjectCommands,
    },
    #[command(about = "Manage virtual organizations and teams")]
    Org {
        #[command(subcommand)]
        command: cli_org::OrgCommands,
    },
    #[command(about = "Interactive AI chat with the platform")]
    Chat {
        message: Option<String>,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    #[command(about = "Show who is online (agents, sessions, peers)")]
    Who {
        #[command(subcommand)]
        command: cli_who::WhoCommands,
    },
    #[command(alias = "commands", about = "Print quick-reference command cheatsheet")]
    Cheatsheet,
    #[command(
        next_help_heading = "Operations",
        about = "Manage agent lifecycle (start, stop, catalog)"
    )]
    Agent {
        #[command(subcommand)]
        command: cli_agent::AgentCommands,
    },
    #[command(about = "Manage individual tasks within plans")]
    Task {
        #[command(subcommand)]
        command: cli_task::TaskCommands,
    },
    #[command(about = "Manage wave groups within plans")]
    Wave {
        #[command(subcommand)]
        command: cli_wave::WaveCommands,
    },
    #[command(about = "Distributed mesh network operations")]
    Mesh {
        #[command(subcommand)]
        command: cli_ops::MeshCommands,
    },
    #[command(about = "Delegate work to remote peers")]
    Delegation {
        #[command(subcommand)]
        command: cli_delegation::DelegationCommands,
    },
    #[command(about = "Notification channels (Telegram, Slack)")]
    Channel {
        #[command(subcommand)]
        command: cli_channel::ChannelCommands,
    },
    #[command(about = "Local AI kernel (Jarvis/Qwen) management")]
    Kernel {
        #[command(subcommand)]
        command: cli_kernel::KernelCommands,
    },
    #[command(about = "Voice input/output and TTS")]
    Voice {
        #[command(subcommand)]
        command: cli_voice::VoiceCommands,
    },
    #[command(about = "Manage isolated workspaces and worktrees")]
    Workspace {
        #[command(subcommand)]
        command: cli_workspace::WorkspaceCommands,
    },
    #[command(about = "Execution run history and management")]
    Run {
        #[command(subcommand)]
        command: cli_run::RunCommands,
    },
    #[command(about = "Save and restore plan checkpoints")]
    Checkpoint {
        #[command(subcommand)]
        command: cli_checkpoint::CheckpointCommands,
    },
    #[command(about = "Plan review and approval workflow")]
    Review {
        #[command(subcommand)]
        command: cli_review::ReviewCommands,
    },
    #[command(about = "Audit trail and compliance reports")]
    Audit {
        #[arg(long, default_value = ".")]
        path: PathBuf,
        #[arg(long)]
        project: Option<String>,
        #[arg(long)]
        output: bool,
        #[arg(long)]
        yes: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    #[command(about = "Cost, token usage, and performance metrics")]
    Metrics {
        #[command(subcommand)]
        command: cli_ops::MetricsCommands,
    },
    #[command(about = "Manage agent capabilities and roles")]
    Capability {
        #[command(subcommand)]
        command: cli_capability::CapabilityCommands,
    },
    #[command(about = "Agent memory (remember, recall, share)")]
    Memory {
        #[command(subcommand)]
        command: cli_memory::MemoryCommands,
    },
    #[command(about = "Knowledge base queries and management")]
    Kb {
        #[command(subcommand)]
        command: cli_kb::KbCommands,
    },
    #[command(about = "Inter-agent message bus")]
    Bus {
        #[command(subcommand)]
        command: cli_bus::BusCommands,
    },
    #[command(about = "Resource locking for concurrent agents")]
    Lock {
        #[command(subcommand)]
        command: cli_lock::LockCommands,
    },
    #[command(about = "Session management")]
    Session {
        #[command(subcommand)]
        command: cli_ops::SessionCommands,
    },
    #[command(about = "Skill registry and invocation")]
    Skill {
        #[command(subcommand)]
        command: cli_skill::SkillCommands,
    },
    #[command(about = "Clean up orphan agents and stale resources")]
    Reap {
        #[command(subcommand)]
        command: cli_reap::ReapCommands,
    },
    #[command(about = "Repository management")]
    Repo {
        #[command(subcommand)]
        command: cli_repo::RepoCommands,
    },
    #[command(about = "Domain and routing management")]
    Domain {
        #[command(subcommand)]
        command: cli_domain::DomainCommands,
    },
    #[command(about = "Alert rules and notifications")]
    Alert {
        #[command(subcommand)]
        command: cli_ops::AlertCommands,
    },
    #[command(about = "Self-build: build, test, deploy the daemon")]
    Build {
        #[command(subcommand)]
        command: cli_build::BuildCommands,
    },
    #[command(about = "Open API documentation in browser")]
    Api,
    #[command(about = "Clean up stale worktree branches")]
    Cleanup,
    #[command(name = "claude", about = "Register a Claude Code session")]
    Claude {
        name: String,
        #[arg(long)]
        parent: Option<String>,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    #[command(name = "copilot", about = "Register a Copilot CLI session")]
    Copilot {
        name: String,
        #[arg(long)]
        parent: Option<String>,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    #[command(name = "ask", about = "Ask an agent a question using alias resolution")]
    Ask {
        alias: String,
        message: Option<String>,
        #[arg(long)]
        list: bool,
        #[arg(long)]
        set: Option<String>,
        #[arg(long)]
        agent: Option<String>,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}
