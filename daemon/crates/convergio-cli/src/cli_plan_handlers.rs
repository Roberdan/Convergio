// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Handler dispatch for plan subcommands — split from cli_plan.rs for 250-line limit.

use crate::cli_error::CliError;
use crate::cli_plan::PlanCommands;

pub async fn dispatch(cmd: PlanCommands) -> Result<(), CliError> {
    match cmd {
        // --- GET-based subcommands ---
        PlanCommands::List { status, limit, human, api_url } => {
            let mut params = Vec::new();
            if let Some(s) = &status {
                params.push(format!("status={s}"));
            }
            if let Some(l) = limit {
                params.push(format!("limit={l}"));
            }
            let qs = if params.is_empty() {
                String::new()
            } else {
                format!("?{}", params.join("&"))
            };
            let url = format!("{api_url}/api/plan-db/list{qs}");
            if let Err(e) = crate::cli_http::fetch_and_print(&url, human).await {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Tree {
            plan_id,
            human,
            api_url,
        } => {
            if human {
                let url = format!("{api_url}/api/plan-db/execution-tree/{plan_id}");
                if let Ok(val) = crate::cli_http::get_and_return(&url).await {
                    crate::cli_plan_tree_fmt::print_execution_tree(&val);
                }
            } else {
                if let Err(e) = crate::cli_http::fetch_and_print(
                    &format!("{api_url}/api/plan-db/execution-tree/{plan_id}"),
                    false,
                )
                .await
                {
                    eprintln!("error: {e}");
                }
            }
        }
        PlanCommands::Show {
            plan_id,
            human,
            api_url,
        } => {
            if human {
                let url = format!("{api_url}/api/plan-db/json/{plan_id}");
                if let Ok(val) = crate::cli_http::get_and_return(&url).await {
                    crate::cli_plan_show::print_plan_human(&val);
                }
            } else if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/json/{plan_id}"),
                false,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Drift {
            plan_id,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/drift-check/{plan_id}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Validate {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plans/{plan_id}/validate"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        // --- POST-based subcommands ---
        PlanCommands::Create {
            project_id,
            name,
            source_file,
            parent,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "project_id": project_id,
                "name": name,
                "source_file": source_file,
                "parent_plan_id": parent,
            });
            if let Err(e) = crate::cli_http::post_and_print(&format!("{api_url}/api/plan-db/create"), &body, human)
                .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Import {
            plan_id,
            spec_file,
            human,
            api_url,
        } => {
            let content = std::fs::read_to_string(&spec_file).map_err(|e| {
                let hint = if e.kind() == std::io::ErrorKind::NotFound {
                    format!(". Does '{spec_file}' exist? Use absolute path or check cwd.")
                } else {
                    String::new()
                };
                CliError::InvalidInput(format!(
                    "cannot read spec file '{spec_file}': {e}{hint}"
                ))
            })?;
            let body = serde_json::json!({
                "plan_id": plan_id,
                "spec": content,
            });
            if let Err(e) = crate::cli_http::post_and_print(&format!("{api_url}/api/plan-db/import"), &body, human)
                .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Start {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/start/{plan_id}"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Complete {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/complete/{plan_id}"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Cancel {
            plan_id,
            reason,
            human,
            api_url,
        } => {
            let body = serde_json::json!({ "reason": reason });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/cancel/{plan_id}"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Approve {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/approve/{plan_id}"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Readiness {
            plan_id,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/readiness/{plan_id}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        PlanCommands::Template => {
            crate::cli_plan_template::print_template();
        }
        PlanCommands::Close {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({});
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/complete/{plan_id}"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
    }
    Ok(())
}
