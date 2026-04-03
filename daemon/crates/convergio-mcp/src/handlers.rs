//! Tool call dispatch: routes each MCP tool name to the daemon HTTP API.

use serde_json::{json, Value};

use crate::http::{http_get, http_post};
use crate::ring::McpError;

/// Dispatch a tool call by name. Returns JSON result or McpError.
pub fn handle_tool_call(
    name: &str,
    args: &Value,
    daemon_url: &str,
    token: Option<&str>,
) -> Result<Value, McpError> {
    match name {
        "cvg_list_plans" => list_plans(daemon_url, token, args),
        "cvg_get_plan" => get_plan(daemon_url, token, args),
        "cvg_update_task" => update_task(daemon_url, token, args),
        "cvg_checkpoint_save" => checkpoint_save(daemon_url, token, args),
        "cvg_list_agents" => list_agents(daemon_url, token),
        "cvg_agent_start" => agent_start(daemon_url, token, args),
        "cvg_agent_complete" => agent_complete(daemon_url, token, args),
        "cvg_mesh_status" => mesh_status(daemon_url, token),
        "cvg_node_readiness" => node_readiness(daemon_url, token),
        "cvg_cost_summary" => cost_summary(daemon_url, token),
        "cvg_kernel_status" => kernel_status(daemon_url, token),
        "cvg_kernel_ask" => kernel_ask(daemon_url, token, args),
        "cvg_notify" => notify(daemon_url, token, args),
        "cvg_restart_node" => restart_node(daemon_url, token, args),
        "cvg_interrupt_agent" => interrupt_agent(daemon_url, token, args),
        _ => Err(McpError::InvalidParams("unknown tool")),
    }
}

// ── Plan handlers ────────────────────────────────────────────────────────────

fn list_plans(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let url = format!("{daemon_url}/api/plan-db/list");
    let body = http_get(&url, token)?;
    let plans = body.get("plans").cloned().unwrap_or(json!([]));
    if let Some(filter) = args.get("status_filter").and_then(|v| v.as_str()) {
        let filtered: Vec<Value> = plans
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .filter(|p| p.get("status").and_then(|s| s.as_str()) == Some(filter))
            .cloned()
            .collect();
        return Ok(json!(filtered));
    }
    Ok(plans)
}

fn get_plan(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let plan_id = args
        .get("plan_id")
        .and_then(|v| v.as_i64())
        .ok_or(McpError::InvalidParams("plan_id is required"))?;
    http_get(&format!("{daemon_url}/api/plan-db/json/{plan_id}"), token)
}

fn update_task(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let task_id = args
        .get("task_id")
        .and_then(|v| v.as_i64())
        .ok_or(McpError::InvalidParams("task_id is required"))?;
    let status = args
        .get("status")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("status is required"))?;
    let payload = json!({
        "task_id": task_id,
        "status": status,
        "summary": args.get("summary").and_then(|v| v.as_str()).unwrap_or("")
    });
    http_post(
        &format!("{daemon_url}/api/plan-db/task/update"),
        token,
        &payload,
    )
}

fn checkpoint_save(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let plan_id = args
        .get("plan_id")
        .and_then(|v| v.as_i64())
        .ok_or(McpError::InvalidParams("plan_id is required"))?;
    http_post(
        &format!("{daemon_url}/api/plan-db/checkpoint/save"),
        token,
        &json!({"plan_id": plan_id}),
    )
}

// ── Agent handlers ───────────────────────────────────────────────────────────

fn list_agents(daemon_url: &str, token: Option<&str>) -> Result<Value, McpError> {
    http_get(&format!("{daemon_url}/api/ipc/agents"), token)
}

fn agent_start(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let name = args
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("name is required"))?;
    let mut payload = json!({"agent_id": name});
    if let Some(task_id) = args.get("task_id").and_then(|v| v.as_i64()) {
        payload["task_id"] = json!(task_id);
    }
    http_post(
        &format!("{daemon_url}/api/plan-db/agent/start"),
        token,
        &payload,
    )
}

fn agent_complete(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let name = args
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("name is required"))?;
    let mut payload = json!({"agent_id": name});
    if let Some(reason) = args.get("exit_reason").and_then(|v| v.as_str()) {
        payload["exit_reason"] = json!(reason);
    }
    http_post(
        &format!("{daemon_url}/api/plan-db/agent/complete"),
        token,
        &payload,
    )
}

// ── Mesh/metrics handlers ────────────────────────────────────────────────────

fn mesh_status(daemon_url: &str, token: Option<&str>) -> Result<Value, McpError> {
    http_get(&format!("{daemon_url}/api/mesh"), token)
}

fn node_readiness(daemon_url: &str, token: Option<&str>) -> Result<Value, McpError> {
    http_get(&format!("{daemon_url}/api/node/readiness"), token)
}

fn cost_summary(daemon_url: &str, token: Option<&str>) -> Result<Value, McpError> {
    let body = http_get(&format!("{daemon_url}/api/plan-db/list"), token)?;
    let plans = body
        .get("plans")
        .and_then(|p| p.as_array())
        .cloned()
        .unwrap_or_default();
    let total_cost: f64 = plans
        .iter()
        .filter_map(|p| p.get("total_cost").and_then(|v| v.as_f64()))
        .sum();
    let active = plans
        .iter()
        .filter(|p| p.get("status").and_then(|s| s.as_str()) == Some("doing"))
        .count();
    Ok(json!({
        "total_cost": total_cost,
        "active_plans": active,
        "total_plans": plans.len(),
    }))
}

// ── Kernel handlers ──────────────────────────────────────────────────────────

fn kernel_status(daemon_url: &str, token: Option<&str>) -> Result<Value, McpError> {
    http_get(&format!("{daemon_url}/api/kernel/status"), token)
}

fn kernel_ask(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let prompt = args
        .get("prompt")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("prompt is required"))?;
    http_post(
        &format!("{daemon_url}/api/kernel/ask"),
        token,
        &json!({"prompt": prompt}),
    )
}

// ── Action handlers ──────────────────────────────────────────────────────────

fn notify(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let message = args
        .get("message")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("message is required"))?;
    let payload = json!({
        "message": message,
        "title": args.get("title").and_then(|v| v.as_str()).unwrap_or("Convergio"),
        "severity": args.get("severity").and_then(|v| v.as_str()).unwrap_or("info"),
    });
    http_post(&format!("{daemon_url}/api/notify"), token, &payload)
}

fn restart_node(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    let target = args
        .get("target")
        .and_then(|v| v.as_str())
        .ok_or(McpError::InvalidParams("target is required"))?;
    http_post(
        &format!("{daemon_url}/api/node/recover"),
        token,
        &json!({"target": target}),
    )
}

fn interrupt_agent(daemon_url: &str, token: Option<&str>, args: &Value) -> Result<Value, McpError> {
    http_post(&format!("{daemon_url}/api/agent/interrupt"), token, args)
}
