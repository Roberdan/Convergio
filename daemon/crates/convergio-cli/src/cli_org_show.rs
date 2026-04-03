use crate::cli_error::CliError;
use crate::cli_http::get_and_return;
use serde_json::{json, Value};

const CYAN: &str = "\x1b[36m";
const GREEN: &str = "\x1b[32m";
const YELLOW: &str = "\x1b[33m";
const RESET: &str = "\x1b[0m";

pub async fn list_orgs(api_url: &str) -> Result<(), CliError> {
    let payload = get_and_return(&format!("{api_url}/api/orgs"))
        .await
        .map_err(|_| CliError::ApiCallFailed("list orgs failed".into()))?;
    println!("{CYAN}ORG ID | STATUS | CEO | MEMBERS | BUDGET{RESET}");
    for org in payload["orgs"].as_array().into_iter().flatten() {
        let id = org["id"].as_str().unwrap_or_default();
        let details = fetch_org_detail(api_url, id).await?;
        println!("{}", format_org_row(&details));
    }
    Ok(())
}

pub async fn show_org(id: &str, api_url: &str) -> Result<(), CliError> {
    let detail = fetch_org_detail(api_url, id).await?;
    let decisions = get_and_return(&format!("{api_url}/api/orgs/{id}/decisions"))
        .await.unwrap_or_else(|_| json!({"decisions": []}));
    let telemetry = get_and_return(&format!("{api_url}/api/orgs/{id}/telemetry?period=day"))
        .await.unwrap_or_else(|_| json!({"aggregate": {}}));
    let digest = get_and_return(&format!("{api_url}/api/orgs/{id}/digest"))
        .await.unwrap_or_else(|_| json!({"digest": null}));
    let out = json!({
        "org": detail["org"],
        "members": detail["members"],
        "services": detail["services"],
        "recent_decisions": decisions["decisions"],
        "telemetry": telemetry["aggregate"],
        "latest_digest": digest["digest"]
    });
    println!(
        "{}",
        serde_json::to_string_pretty(&out).unwrap_or_else(|_| out.to_string())
    );
    Ok(())
}

pub async fn org_plans(slug: &str, api_url: &str) -> Result<(), CliError> {
    let payload = get_and_return(&format!("{api_url}/api/orgs/{slug}/plans"))
        .await
        .map_err(|_| CliError::ApiCallFailed("get org plans failed".into()))?;
    let plans = payload["plans"].as_array();
    if plans.map(|p| p.is_empty()).unwrap_or(true) {
        println!("No plans linked to org '{slug}'");
        return Ok(());
    }
    println!("{CYAN}ID | NAME | STATUS | PROGRESS{RESET}");
    for p in plans.into_iter().flatten() {
        let id = p["id"].as_i64().unwrap_or(0);
        let name = p["name"].as_str().unwrap_or("-");
        let status = p["status"].as_str().unwrap_or("-");
        let done = p["tasks_done"].as_i64().unwrap_or(0);
        let total = p["tasks_total"].as_i64().unwrap_or(0);
        let color = if status == "completed" { GREEN } else { YELLOW };
        println!("#{id} | {name} | {color}{status}{RESET} | {done}/{total}");
    }
    Ok(())
}

pub async fn org_chart(slug: Option<&str>, api_url: &str) -> Result<(), CliError> {
    let url = match slug {
        Some(s) => format!("{api_url}/api/orgs/{s}/orgchart"),
        None => format!("{api_url}/api/orgs/chart"),
    };
    let payload = get_and_return(&url)
        .await
        .map_err(|_| CliError::ApiCallFailed("get orgchart failed".into()))?;
    // Global chart returns "chart" (ASCII); per-slug returns structured JSON
    if let Some(chart) = payload["chart"].as_str() {
        println!("{chart}");
    } else {
        render_single_orgchart(&payload);
    }
    Ok(())
}

/// Render a single org's chart from the per-slug JSON response.
fn render_single_orgchart(data: &Value) {
    let org = &data["org"];
    let name = org["id"].as_str().unwrap_or("unknown");
    let status = org["status"].as_str().unwrap_or("-");
    let ceo = org["ceo_agent"].as_str().unwrap_or("-");
    println!("{CYAN}{name}{RESET} ({status})");
    println!("  CEO: {GREEN}{ceo}{RESET}");
    for dept in data["departments"].as_array().into_iter().flatten() {
        let dname = dept["name"].as_str().unwrap_or("General");
        println!("  \u{251c}\u{2500}\u{2500} {CYAN}{dname}{RESET}");
        for agent in dept["agents"].as_array().into_iter().flatten() {
            let aname = agent["agent"].as_str().unwrap_or("-");
            let role = agent["role"].as_str().unwrap_or("-");
            println!("  \u{2502}   \u{2514}\u{2500}\u{2500} {aname} ({YELLOW}{role}{RESET})");
        }
    }
    if let Some(plans) = data["plans"].as_array() {
        if !plans.is_empty() {
            println!("  Plans:");
            for p in plans {
                let pname = p["title"].as_str().or(p["name"].as_str()).unwrap_or("-");
                let pstatus = p["status"].as_str().unwrap_or("-");
                println!("    - {pname} [{YELLOW}{pstatus}{RESET}]");
            }
        }
    }
}

pub fn format_org_row(org_detail: &Value) -> String {
    let id = org_detail["org"]["id"].as_str()
        .or_else(|| org_detail["id"].as_str()).unwrap_or("-");
    let status = org_detail["org"]["status"].as_str()
        .or_else(|| org_detail["status"].as_str()).unwrap_or("-");
    let ceo = org_detail["org"]["ceo_agent"].as_str()
        .or_else(|| org_detail["ceo_agent"].as_str()).unwrap_or("-");
    let members = org_detail["member_count"].as_u64().unwrap_or(0);
    let budget = org_detail["budget_usage_pct"].as_f64().unwrap_or(0.0);
    let color = if status == "active" { GREEN } else { YELLOW };
    format!("{id} | {color}{status}{RESET} | {ceo} | {members} | {budget:.1}%")
}

async fn fetch_org_detail(api_url: &str, id: &str) -> Result<Value, CliError> {
    let detail = get_and_return(&format!("{api_url}/api/orgs/{id}"))
        .await
        .map_err(|_| CliError::ApiCallFailed("get org detail failed".into()))?;
    let member_count = detail["members"].as_array().map(|m| m.len()).unwrap_or(0);
    let budget = detail["org"]["budget"].as_f64().unwrap_or(0.0).max(1.0);
    let agg = get_and_return(&format!("{api_url}/api/orgs/{id}/telemetry?period=day"))
        .await
        .unwrap_or_else(|_| json!({"aggregate": {"cost": 0.0}}));
    let cost = agg["aggregate"]["cost"].as_f64().unwrap_or(0.0);
    Ok(json!({
        "org": detail["org"],
        "members": detail["members"],
        "services": detail["services"],
        "member_count": member_count,
        "budget_usage_pct": (cost / budget) * 100.0
    }))
}
