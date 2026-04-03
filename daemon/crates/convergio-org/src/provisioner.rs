//! Org provisioner — creates org, plan, agents, and tasks via daemon HTTP API.

use serde_json::{json, Value};

use super::factory::OrgBlueprint;

/// Outcome of provisioning an org from a blueprint.
pub struct ProvisionResult {
    pub org_id: String,
    pub plan_id: i64,
    pub agents_created: usize,
    pub night_agents_scheduled: usize,
    pub tasks_created: usize,
}

/// POST helper with 10s timeout and optional bearer auth from env.
fn api_post(url: &str, body: &Value) -> Result<Value, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| format!("http client build: {e}"))?;

    let token = std::env::var("CONVERGIO_AUTH_TOKEN").ok();
    let mut req = client.post(url).json(body);
    if let Some(t) = &token {
        req = req.bearer_auth(t);
    }

    let resp = req.send().map_err(|e| format!("POST {url}: {e}"))?;
    let status = resp.status();
    let text = resp.text().map_err(|e| format!("read body: {e}"))?;
    if !status.is_success() {
        return Err(format!("POST {url} -> {status}: {text}"));
    }
    serde_json::from_str(&text).map_err(|e| format!("parse response from {url}: {e}"))
}

/// Provision a full org from a blueprint via the daemon HTTP API.
pub fn provision_org(
    blueprint: &OrgBlueprint,
    daemon_url: &str,
) -> Result<ProvisionResult, String> {
    let org_body = json!({
        "id": blueprint.slug,
        "name": blueprint.name,
        "mission": blueprint.mission,
        "objectives": blueprint.mission,
        "ceo_agent": blueprint.ceo_agent,
        "budget": blueprint.budget_usd,
        "status": "active",
    });
    let org_resp = api_post(&format!("{daemon_url}/api/orgs"), &org_body)?;
    let org_id = org_resp
        .get("org_id")
        .or_else(|| org_resp.get("id"))
        .and_then(|v| {
            v.as_str()
                .map(String::from)
                .or_else(|| v.as_i64().map(|n| n.to_string()))
        })
        .ok_or("missing org_id in response")?;

    let mut agents_created: usize = 0;
    for dept in &blueprint.departments {
        for agent in &dept.agents {
            let agent_body = json!({
                "agent_id": agent.name,
                "host": "org-provisioner",
                "agent_type": "claude",
                "metadata": json!({
                    "org_id": org_id,
                    "department": dept.name,
                    "model": agent.model,
                    "capabilities": agent.capabilities,
                }).to_string(),
            });
            let url = format!("{daemon_url}/api/ipc/agents/register");
            if api_post(&url, &agent_body).is_ok() {
                agents_created += 1;
            }
        }
    }

    let plan_body = json!({
        "title": format!("Bootstrap: {}", blueprint.name),
        "description": blueprint.mission,
    });
    let plan_resp = api_post(&format!("{daemon_url}/api/plan-db/create"), &plan_body)?;
    let plan_id = plan_resp
        .get("plan_id")
        .or_else(|| plan_resp.get("id"))
        .and_then(|v| v.as_i64())
        .ok_or("missing plan_id in response")?;

    let mut tasks: Vec<String> = Vec::new();
    if blueprint.repo_path.is_some() {
        tasks.push("Analyze codebase and document architecture".into());
    }
    tasks.push("Set up monitoring and alerting".into());
    for dept in &blueprint.departments {
        tasks.push(format!("{}: Initial setup and configuration", dept.name));
    }

    let mut tasks_created: usize = 0;
    for title in &tasks {
        let task_body = json!({
            "plan_id": plan_id, "title": title, "status": "pending",
        });
        let url = format!("{daemon_url}/api/plan-db/task/create");
        if api_post(&url, &task_body).is_ok() {
            tasks_created += 1;
        }
    }

    let mut night_agents_scheduled: usize = 0;
    for na in &blueprint.night_agents {
        let task_body = json!({
            "plan_id": plan_id,
            "title": format!("Night: {} ({} {})", na.name, na.time, na.schedule),
            "status": "pending",
            "metadata": json!({
                "night_agent": true, "schedule": na.schedule,
                "time": na.time, "model": na.model,
            }).to_string(),
        });
        let url = format!("{daemon_url}/api/plan-db/task/create");
        if api_post(&url, &task_body).is_ok() {
            night_agents_scheduled += 1;
        }
    }

    Ok(ProvisionResult {
        org_id,
        plan_id,
        agents_created,
        night_agents_scheduled,
        tasks_created,
    })
}
