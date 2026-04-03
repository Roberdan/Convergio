use crate::cli_error::CliError;
use clap::Subcommand;
use serde_json::{json, Value};

#[derive(Debug, Subcommand)]
pub enum OrgCommands {
    /// Create a new org and bootstrap its CEO agent session
    Create {
        /// Org identifier
        name: String,
        /// Org mission
        #[arg(long)]
        mission: String,
        /// Org objectives
        #[arg(long)]
        objectives: String,
        /// Daily org budget
        #[arg(long)]
        budget: f64,
        /// CEO agent name
        #[arg(long, default_value = "ceo")]
        ceo_agent: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List orgs with status, CEO, members and budget usage
    List {
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show one org with details
    Show {
        id: String,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List plans belonging to an org
    Plans {
        slug: String,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Show global orgchart (all orgs) or single org chart
    Chart {
        /// Org slug (omit for global ecosystem view)
        slug: Option<String>,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a virtual organization from a mission/goal
    CreateOrg {
        name: String,
        #[arg(long)]
        mission: String,
        #[arg(long, default_value = "50")]
        budget: f64,
        #[arg(long)]
        yes: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Create a virtual organization from an existing repo
    CreateOrgFrom {
        path: String,
        #[arg(long)]
        name: Option<String>,
        #[arg(long, default_value = "50")]
        budget: f64,
        #[arg(long)]
        yes: bool,
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: OrgCommands) -> Result<(), CliError> {
    match cmd {
        OrgCommands::Create {
            name,
            mission,
            objectives,
            budget,
            ceo_agent,
            api_url,
        } => create_org_and_spawn_ceo(&name, &mission, &objectives, budget, &ceo_agent, &api_url).await,
        OrgCommands::List { api_url } => crate::cli_org_show::list_orgs(&api_url).await,
        OrgCommands::Show { id, api_url } => crate::cli_org_show::show_org(&id, &api_url).await,
        OrgCommands::Plans { slug, api_url } => crate::cli_org_show::org_plans(&slug, &api_url).await,
        OrgCommands::Chart { slug, api_url } => crate::cli_org_show::org_chart(slug.as_deref(), &api_url).await,
        OrgCommands::CreateOrg { name, mission, budget, yes, api_url } => {
            crate::cli_create_org::handle_create_org(&name, &mission, budget, yes, &api_url).await
        }
        OrgCommands::CreateOrgFrom { path, name, budget, yes, api_url } => {
            crate::cli_create_org::handle_create_org_from(&path, name.as_deref(), budget, yes, &api_url).await
        }
    }
}

async fn create_org_and_spawn_ceo(
    name: &str,
    mission: &str,
    objectives: &str,
    budget: f64,
    ceo_agent: &str,
    api_url: &str,
) -> Result<(), CliError> {
    let client = reqwest::Client::new();
    let create_body = json!({
        "id": name,
        "mission": mission,
        "objectives": objectives,
        "ceo_agent": ceo_agent,
        "budget": budget,
    });
    let create_resp = client
        .post(format!("{api_url}/api/orgs"))
        .json(&create_body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("failed to create org: {e}")))?;
    let create_status = create_resp.status();
    let create_json: Value = create_resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("failed to decode org response: {e}")))?;
    if !create_status.is_success() {
        return Err(CliError::ApiCallFailed(format!(
            "org create failed with status {create_status}: {create_json}"
        )));
    }
    let start_body = json!({"agent_id": ceo_agent, "name": ceo_agent, "task_id": Value::Null});
    let start_resp = client
        .post(format!("{api_url}/api/plan-db/agent/start"))
        .json(&start_body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("failed to start ceo agent: {e}")))?;
    let start_status = start_resp.status();
    let start_json: Value = start_resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("failed to decode ceo start response: {e}")))?;
    if !start_status.is_success() {
        return Err(CliError::ApiCallFailed(format!(
            "ceo start failed with status {start_status}: {start_json}"
        )));
    }
    let out = json!({
        "ok": true,
        "org": create_json,
        "ceo_spawn": start_json,
    });
    println!(
        "{}",
        serde_json::to_string_pretty(&out).unwrap_or_else(|_| out.to_string())
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use clap::Parser;

    #[derive(Debug, Parser)]
    struct TestCli {
        #[command(subcommand)]
        cmd: OrgCommands,
    }

    #[test]
    fn parse_org_create_command() {
        let cli = TestCli::parse_from([
            "cvg",
            "create",
            "acme-labs",
            "--mission",
            "Build autonomous orgs",
            "--objectives",
            "Ship quickly",
            "--budget",
            "1200",
        ]);
        match cli.cmd {
            OrgCommands::Create {
                name,
                mission,
                objectives,
                budget,
                ceo_agent,
                ..
            } => {
                assert_eq!(name, "acme-labs");
                assert_eq!(mission, "Build autonomous orgs");
                assert_eq!(objectives, "Ship quickly");
                assert_eq!(budget, 1200.0);
                assert_eq!(ceo_agent, "ceo");
            }
            _ => panic!("expected create command"),
        }
    }

    #[test]
    fn parse_org_list_command() {
        let cli = TestCli::parse_from(["cvg", "list"]);
        match cli.cmd {
            OrgCommands::List { api_url } => {
                assert_eq!(api_url, "http://localhost:8420");
            }
            _ => panic!("expected list command"),
        }
    }

    #[test]
    fn format_org_list_contains_expected_columns() {
        let rendered = crate::cli_org_show::format_org_row(&serde_json::json!({
            "id": "fitness-project",
            "status": "active",
            "ceo_agent": "fitness-ceo",
            "member_count": 7,
            "budget_usage_pct": 60.0
        }));
        assert!(rendered.contains("fitness-project"));
        assert!(rendered.contains("fitness-ceo"));
        assert!(rendered.contains("60.0%"));
    }
}
