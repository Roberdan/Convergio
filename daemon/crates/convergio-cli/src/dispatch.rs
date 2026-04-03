// Command dispatch — routes parsed CLI commands to handlers.
// Pure HTTP client: no daemon internals.

use crate::cli_commands::Commands;
use crate::cli_error::CliError;
use crate::{
    cli_agent_format, cli_ask, cli_audit, cli_audit_project, cli_bus, cli_capability, cli_channel,
    cli_chat, cli_checkpoint, cli_delegation, cli_domain, cli_kb, cli_kernel, cli_launch, cli_lock,
    cli_memory, cli_ops, cli_org, cli_plan, cli_project, cli_reap, cli_repo, cli_review, cli_run,
    cli_setup, cli_skill, cli_status, cli_task, cli_voice, cli_wave, cli_who, cli_workspace,
};
use std::process::ExitCode;

pub async fn dispatch(command: Commands) -> ExitCode {
    match command {
        Commands::Setup { defaults } => exit_on_err(cli_setup::handle_setup(defaults).await),
        Commands::Plan { command } => exit_on_err(cli_plan::handle(command).await),
        Commands::Task { command } => exit_on_err(cli_task::handle(command).await),
        Commands::Wave { command } => exit_on_err(cli_wave::handle(command).await),
        Commands::Agent { command } => exit_on_err(cli_agent_format::dispatch(command).await),
        Commands::Kb { command } => exit_on_err(cli_kb::handle(command).await),
        Commands::Status { api_url } => exit_on_err(cli_status::handle(&api_url).await),
        Commands::Chat { message, api_url } => {
            exit_on_err(cli_chat::handle(&api_url, message).await)
        }
        Commands::Channel { command } => exit_on_err(cli_channel::handle(command).await),
        Commands::Capability { command } => exit_on_err(cli_capability::handle(command).await),
        Commands::Voice { command } => exit_on_err(cli_voice::handle(command).await),
        Commands::Memory { command } => exit_on_err(cli_memory::handle(command).await),
        Commands::Run { command } => exit_on_err(cli_run::handle(command).await),
        Commands::Mesh { command } => {
            cli_ops::handle_mesh(command).await;
            ExitCode::SUCCESS
        }
        Commands::Session { command } => {
            cli_ops::handle_session(command).await;
            ExitCode::SUCCESS
        }
        Commands::Checkpoint { command } => {
            cli_checkpoint::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Lock { command } => {
            cli_lock::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Review { command } => {
            cli_review::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Audit {
            path,
            project,
            output,
            yes,
            api_url,
        } => {
            if let Some(project_id) = project {
                exit_on_err(cli_audit_project::handle(&project_id, output, yes, &api_url).await)
            } else {
                exit_on_err(cli_audit::handle(path))
            }
        }
        Commands::Skill { command } => exit_on_err(cli_skill::handle(command).await),
        Commands::Bus { command } => {
            cli_bus::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Project { command } => exit_on_err(cli_project::handle(command).await),
        Commands::Metrics { command } => {
            cli_ops::handle_metrics(command).await;
            ExitCode::SUCCESS
        }
        Commands::Alert { command } => {
            cli_ops::handle_alert(command).await;
            ExitCode::SUCCESS
        }
        Commands::Domain { command } => exit_on_err(cli_domain::dispatch(command).await),
        Commands::Org { command } => exit_on_err(cli_org::handle(command).await),
        Commands::Workspace { command } => {
            cli_workspace::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Who { command } => {
            exit_on_err(cli_who::handle(command, "http://localhost:8420").await)
        }
        Commands::Delegation { command } => {
            exit_on_err(cli_delegation::handle(command, "http://localhost:8420").await)
        }
        Commands::Reap { command } => {
            cli_reap::handle(command).await;
            ExitCode::SUCCESS
        }
        Commands::Repo { command } => exit_on_err(cli_repo::handle(command).await),
        Commands::Kernel { command } => cli_kernel::dispatch(command).await,
        Commands::Cheatsheet => {
            crate::cli_cheatsheet::print_cheatsheet();
            ExitCode::SUCCESS
        }
        Commands::Api => {
            crate::cli_api_list::print_api_list();
            ExitCode::SUCCESS
        }
        Commands::Cleanup => exit_on_err(crate::cli_cleanup::handle().await),
        Commands::Claude {
            name,
            parent,
            api_url,
        } => exit_on_err(
            cli_launch::handle(cli_launch::LaunchCommands::Claude {
                name,
                parent,
                api_url,
            })
            .await,
        ),
        Commands::Copilot {
            name,
            parent,
            api_url,
        } => exit_on_err(
            cli_launch::handle(cli_launch::LaunchCommands::Copilot {
                name,
                parent,
                api_url,
            })
            .await,
        ),
        Commands::Ask {
            alias,
            message,
            list,
            set,
            agent,
            api_url,
        } => exit_on_err(cli_ask::handle(alias, message, list, set, agent, &api_url).await),
    }
}

fn exit_on_err(result: Result<(), CliError>) -> ExitCode {
    match result {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            ExitCode::from(e.exit_code() as u8)
        }
    }
}
