// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Project subcommands for the cvg CLI — local filesystem ops + daemon HTTP API.

use crate::cli_error::CliError;
use clap::Subcommand;
use std::path::PathBuf;

#[derive(Debug, Subcommand)]
pub enum ProjectCommands {
    /// Scaffold and initialize a new project repository
    Init {
        /// Project name (alphanumeric + hyphens)
        name: String,
        /// Language: rust, typescript, python
        #[arg(long, default_value = "rust")]
        lang: String,
        /// License: mit, apache2, gpl3
        #[arg(long, default_value = "mit")]
        license: String,
        /// Visibility: public, private
        #[arg(long, default_value = "public")]
        visibility: String,
        /// Organization ID
        #[arg(long, default_value = "default")]
        org_id: String,
        /// Optional template name from org manifest
        #[arg(long)]
        template: Option<String>,
        /// Create local repo only (no GitHub)
        #[arg(long)]
        local: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a new project with input folder and output directory
    Create {
        /// Project name
        #[arg(long)]
        name: String,
        /// Input folder path (must exist and be readable)
        #[arg(long)]
        input: PathBuf,
        /// Skip interactive confirmation
        #[arg(long)]
        yes: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List all projects as JSON
    List {
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show a single project with deliverable count
    Show {
        /// Project ID
        id: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show hierarchical plan tree for a project
    Plans {
        /// Project ID
        id: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: ProjectCommands) -> Result<(), CliError> {
    match cmd {
        ProjectCommands::Init {
            name,
            lang,
            license,
            visibility,
            org_id,
            template,
            local,
            api_url,
        } => {
            crate::cli_project_init::handle_init(
                &name,
                &lang,
                &license,
                &visibility,
                &org_id,
                template.as_deref(),
                local,
                &api_url,
            )
            .await
        }
        ProjectCommands::Create {
            name,
            input,
            yes,
            api_url,
        } => crate::cli_project_handlers::handle_create(&name, &input, yes, &api_url).await,
        ProjectCommands::List { api_url } => {
            crate::cli_project_handlers::handle_list(&api_url).await
        }
        ProjectCommands::Show { id, api_url } => {
            crate::cli_project_handlers::handle_show(&id, &api_url).await
        }
        ProjectCommands::Plans { id, api_url } => {
            crate::cli_project_handlers::handle_plans(&id, &api_url).await
        }
    }
}
