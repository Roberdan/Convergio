// cvg who — show active agents, delegations, and what's being worked on.
// Why: Plan 706 — no way to know who's working on what. This is the answer.

use crate::cli_error::CliError;
use crate::cli_http;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum WhoCommands {
    /// Show all active agents across all nodes
    Agents,
    /// Show who is working on a specific plan
    Plan { plan_id: i64 },
    /// Prune stale/zombie workers
    Prune,
}

fn api_err(code: i32) -> CliError {
    CliError::ApiCallFailed(format!("daemon returned error (code {code})"))
}

pub async fn handle(cmd: WhoCommands, api_url: &str) -> Result<(), CliError> {
    match cmd {
        WhoCommands::Agents => {
            let url = format!("{api_url}/api/workers");
            let body = cli_http::get_and_return(&url).await.map_err(api_err)?;
            let workers = body.get("workers").and_then(|w| w.as_array());
            match workers {
                Some(list) if !list.is_empty() => {
                    println!(
                        "{:<30} {:<15} {:<10} {:<8} DESCRIPTION",
                        "AGENT", "HOST", "MODEL", "PLAN"
                    );
                    println!("{}", "-".repeat(90));
                    for w in list {
                        let agent = w["agent_id"].as_str().unwrap_or("?");
                        let host = w["host"].as_str().unwrap_or("?");
                        let model = w["model"].as_str().unwrap_or("?");
                        let plan = w["plan_id"]
                            .as_i64()
                            .map(|v| v.to_string())
                            .unwrap_or("-".into());
                        let desc = w["description"].as_str().unwrap_or("");
                        println!(
                            "{:<30} {:<15} {:<10} {:<8} {}",
                            agent,
                            host,
                            model,
                            plan,
                            &desc[..desc.len().min(40)]
                        );
                    }
                }
                _ => println!("No active workers."),
            }
            // IPC agent tree (parentage hierarchy)
            let tree_url = format!("{api_url}/api/ipc/agents/tree");
            if let Ok(tb) = cli_http::get_and_return(&tree_url).await {
                if let Some(tree) = tb["tree"].as_array() {
                    if !tree.is_empty() {
                        println!("\nIPC Agent Tree ({} registered):", tb["total"].as_i64().unwrap_or(0));
                        for node in tree {
                            print_tree_node(node, 0);
                        }
                    }
                }
            }
            // Online peers
            let peers_url = format!("{api_url}/api/heartbeat/status");
            if let Ok(pb) = cli_http::get_and_return(&peers_url).await {
                if let Some(peers) = pb["peers"].as_array() {
                    let online: Vec<_> = peers
                        .iter()
                        .filter(|p| p["age_secs"].as_i64().map(|a| a < 300).unwrap_or(false))
                        .collect();
                    if !online.is_empty() {
                        println!("\nOnline peers ({}):", online.len());
                        for p in &online {
                            println!(
                                "  {} ({}s ago)",
                                p["peer_name"].as_str().unwrap_or("?"),
                                p["age_secs"].as_i64().unwrap_or(0)
                            );
                        }
                    }
                }
            }
            Ok(())
        }
        WhoCommands::Plan { plan_id } => {
            // Workers on this plan
            let url = format!("{api_url}/api/workers");
            let body = cli_http::get_and_return(&url).await.map_err(api_err)?;
            if let Some(list) = body["workers"].as_array() {
                let active: Vec<_> = list
                    .iter()
                    .filter(|w| w["plan_id"].as_i64() == Some(plan_id))
                    .collect();
                if active.is_empty() {
                    println!("No active workers on plan {plan_id}.");
                } else {
                    println!("Workers on plan {plan_id}:");
                    for w in &active {
                        println!(
                            "  {} on {} ({})",
                            w["agent_id"].as_str().unwrap_or("?"),
                            w["host"].as_str().unwrap_or("?"),
                            w["model"].as_str().unwrap_or("?")
                        );
                    }
                }
            }
            // In-progress tasks
            let tree_url = format!("{api_url}/api/plan-db/json/{plan_id}");
            if let Ok(ctx) = cli_http::get_and_return(&tree_url).await {
                if let Some(tasks) = ctx["tasks"].as_array() {
                    let active: Vec<_> = tasks
                        .iter()
                        .filter(|t| t["status"].as_str() == Some("in_progress"))
                        .collect();
                    if !active.is_empty() {
                        println!("\nTasks in progress:");
                        for t in &active {
                            let title = t["title"].as_str().unwrap_or("");
                            println!(
                                "  {} [{}]: {}...",
                                t["task_id"].as_str().unwrap_or("?"),
                                t["executor_host"].as_str().unwrap_or("local"),
                                &title[..title.len().min(60)]
                            );
                        }
                    }
                }
            }
            Ok(())
        }
        WhoCommands::Prune => {
            let url = format!("{api_url}/api/workers");
            let body = cli_http::get_and_return(&url).await.map_err(api_err)?;
            if let Some(list) = body["workers"].as_array() {
                let mut pruned = 0;
                for w in list {
                    let agent = w["agent_id"].as_str().unwrap_or("?");
                    let complete_url = format!("{api_url}/api/plan-db/agent/complete");
                    let payload = serde_json::json!({"agent_id": agent, "status": "pruned"});
                    if cli_http::post_and_return(&complete_url, &payload)
                        .await
                        .is_ok()
                    {
                        pruned += 1;
                        println!("  pruned: {agent}");
                    }
                }
                println!("Pruned {pruned} stale workers.");
            }
            Ok(())
        }
    }
}

fn print_tree_node(node: &serde_json::Value, depth: usize) {
    let indent = "  ".repeat(depth);
    let prefix = if depth == 0 { "●" } else { "└──" };
    let name = node["name"].as_str().unwrap_or("?");
    let kind = node["type"].as_str().unwrap_or("?");
    let status = node["status"].as_str().unwrap_or("?");
    let host = node["host"].as_str().unwrap_or("");
    let status_icon = match status {
        "active" => "✓",
        "inactive" => "✗",
        _ => "?",
    };
    println!("  {indent}{prefix} {name} [{kind}] {status_icon} {host}");
    if let Some(children) = node["children"].as_array() {
        for child in children {
            print_tree_node(child, depth + 1);
        }
    }
}
