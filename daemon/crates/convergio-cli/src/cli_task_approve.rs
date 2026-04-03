// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Handler for `cvg task approve <task_id>` — finds deliverable linked to task,
// then approves it via the daemon HTTP API.

use crate::cli_error::CliError;
use crate::message_error::MessageResult;
use serde_json::Value;

/// Approve the deliverable linked to a task.
/// Flow: GET /api/deliverables?task_id=<id> → find deliverable → POST approve.
pub async fn handle(
    task_id: i64,
    comment: Option<String>,
    human: bool,
    api_url: &str,
) -> Result<(), CliError> {
    let deliverable = find_deliverable(task_id, api_url)
        .await
        .map_err(|e| CliError::NotFound(e.to_string()))?;

    let id = deliverable["id"].as_i64().unwrap_or(0);
    let approved_by = comment.unwrap_or_else(|| "cli".to_string());

    let body = serde_json::json!({ "approved_by": approved_by });
    let url = format!("{api_url}/api/deliverables/{id}/approve");

    let client = reqwest::Client::new();
    let resp = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;

    let status = resp.status();
    let val: Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;

    if human {
        print_approval_human(&val);
    } else {
        println!("{val}");
    }

    if !status.is_success() {
        return Err(CliError::NotFound(format!(
            "daemon returned status {status}"
        )));
    }
    Ok(())
}

/// Find the deliverable linked to a task via GET /api/deliverables?task_id=<id>.
/// Returns the first deliverable or an error message.
async fn find_deliverable(task_id: i64, api_url: &str) -> MessageResult<Value> {
    let url = format!("{api_url}/api/deliverables?task_id={task_id}");
    let resp = reqwest::get(&url)
        .await
        .map_err(|e| format!("error connecting to daemon: {e}"))?;

    if !resp.status().is_success() {
        return Err(format!("daemon returned status {}", resp.status()).into());
    }

    let list: Value = resp
        .json()
        .await
        .map_err(|e| format!("error parsing deliverables response: {e}"))?;

    let arr = list
        .as_array()
        .ok_or_else(|| "unexpected response format: expected array".to_string())?;

    if arr.is_empty() {
        return Err(format!(
            "no deliverable linked to task {task_id}. \
             Create one first with: cvg deliverable create --task-id {task_id}"
        )
        .into());
    }

    // Return the most recent (first, since ordered by id DESC)
    Ok(arr[0].clone())
}

/// Human-readable output for deliverable approval confirmation.
fn print_approval_human(val: &Value) {
    let name = val["name"].as_str().unwrap_or("(unknown)");
    let path = val["output_path"].as_str().unwrap_or("(none)");
    let version = val["version"].as_i64().unwrap_or(0);
    let status = val["status"].as_str().unwrap_or("approved");

    println!("Deliverable approved:");
    println!("  Name:    {name}");
    println!("  Path:    {path}");
    println!("  Version: v{version}");
    println!("  Status:  {status}");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn print_approval_human_formats_correctly() {
        let val = serde_json::json!({
            "id": 42,
            "name": "analysis-report",
            "output_path": "/data/output/2026-03-22_analysis-report_v1",
            "version": 1,
            "status": "approved",
        });
        // Should not panic
        print_approval_human(&val);
    }

    #[test]
    fn print_approval_human_handles_missing_fields() {
        let val = serde_json::json!({"id": 1});
        // Should not panic; uses defaults
        print_approval_human(&val);
    }
}
