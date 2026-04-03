// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Wave CLI handler implementations — called from cli_wave::handle().
// Split from cli_wave.rs to stay under the 250-line file limit.

use crate::cli_error::CliError;

/// Look up the active workspace_id for a given wave in a plan.
/// Returns None (and prints an error) if not found.
async fn find_workspace_id(api_url: &str, plan_id: i64, wave_id: i64) -> Option<String> {
    let list_url = format!("{api_url}/api/workspace/list?plan_id={plan_id}");
    let list_resp = match crate::cli_http::get_and_return(&list_url).await {
        Ok(v) => v,
        Err(code) => {
            eprintln!("error listing workspaces (exit {code})");
            return None;
        }
    };
    list_resp
        .get("workspaces")
        .and_then(|ws| ws.as_array())
        .and_then(|arr| {
            arr.iter().find(|w| {
                (w.get("wave_db_id").and_then(|v| v.as_i64()) == Some(wave_id))
                    && w.get("status")
                        .and_then(|v| v.as_str())
                        .is_none_or(|s| s == "active")
            })
        })
        .and_then(|w| w.get("workspace_id"))
        .and_then(|v| v.as_str())
        .map(str::to_owned)
}

/// Create wave in plan-db, then provision a workspace for the new wave.
pub async fn handle_create(
    plan_id: i64,
    wave_id: String,
    name: String,
    human: bool,
    api_url: String,
) -> Result<(), CliError> {
    let create_body = serde_json::json!({
        "plan_id": plan_id,
        "wave_id": wave_id,
        "name": name,
    });
    let wave_resp = crate::cli_http::post_and_return(
        &format!("{api_url}/api/plan-db/wave/create"),
        &create_body,
    )
    .await
    .map_err(|code| CliError::ApiCallFailed(format!("wave create failed (exit {code})")))?;

    // Provision workspace using the wave_db_id returned by the create endpoint.
    if let Some(wave_db_id) = wave_resp.get("wave_db_id").and_then(|v| v.as_i64()) {
        let ws_body = serde_json::json!({
            "plan_id": plan_id,
            "wave_db_id": wave_db_id,
        });
        match crate::cli_http::post_and_return(&format!("{api_url}/api/workspace/create"), &ws_body)
            .await
        {
            Ok(ws_resp) => {
                let combined = serde_json::json!({
                    "ok": true,
                    "wave": wave_resp,
                    "workspace": ws_resp.get("workspace"),
                });
                crate::cli_http::print_value(&combined, human);
            }
            Err(code) => {
                eprintln!("warning: wave created but workspace provisioning failed (exit {code})");
                crate::cli_http::print_value(&wave_resp, human);
            }
        }
    } else {
        crate::cli_http::print_value(&wave_resp, human);
    }
    Ok(())
}

/// Trigger the workspace release pipeline instead of the legacy wave/merge endpoint.
pub async fn handle_merge(
    plan_id: i64,
    wave_id: i64,
    human: bool,
    api_url: String,
) -> Result<(), CliError> {
    let workspace_id = find_workspace_id(&api_url, plan_id, wave_id)
        .await
        .ok_or_else(|| {
            CliError::NotFound(format!(
                "no active workspace found for wave {wave_id} in plan {plan_id}"
            ))
        })?;
    let release_body = serde_json::json!({"workspace_id": workspace_id});
    crate::cli_http::post_and_print(
        &format!("{api_url}/api/workspace/release"),
        &release_body,
        human,
    )
    .await
}

/// Run mechanical quality gates first; only call Thor if all gates pass.
pub async fn handle_validate(
    wave_id: i64,
    plan_id: i64,
    human: bool,
    api_url: String,
) -> Result<(), CliError> {
    let workspace_id = find_workspace_id(&api_url, plan_id, wave_id).await;
    if let Some(ws_id) = workspace_id {
        let qg_body = serde_json::json!({"workspace_id": ws_id});
        match crate::cli_http::post_and_return(
            &format!("{api_url}/api/workspace/quality-gate"),
            &qg_body,
        )
        .await
        {
            Ok(qg_resp) => {
                let all_passed = qg_resp
                    .get("all_passed")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                if !all_passed {
                    crate::cli_http::print_value(&qg_resp, human);
                    return Err(CliError::NotFound(
                        "quality gates failed — Thor validation blocked".into(),
                    ));
                }
            }
            Err(code) => {
                eprintln!("quality gate check failed (exit {code}); proceeding to Thor anyway");
            }
        }
    } else {
        eprintln!("no workspace found for wave {wave_id}; skipping quality gates");
    }
    let thor_body = serde_json::json!({"wave_id": wave_id, "scope": "wave"});
    crate::cli_http::post_and_print(
        &format!("{api_url}/api/plans/{plan_id}/validate"),
        &thor_body,
        human,
    )
    .await
}

/// Release alias — convenience wrapper around the workspace release pipeline.
pub async fn handle_release(
    wave_id: i64,
    plan_id: i64,
    repo: String,
    human: bool,
    api_url: String,
) -> Result<(), CliError> {
    let workspace_id = find_workspace_id(&api_url, plan_id, wave_id)
        .await
        .ok_or_else(|| {
            CliError::NotFound(format!(
                "no active workspace found for wave {wave_id} in plan {plan_id}"
            ))
        })?;
    let release_body = serde_json::json!({"workspace_id": workspace_id, "repo": repo});
    crate::cli_http::post_and_print(
        &format!("{api_url}/api/workspace/release"),
        &release_body,
        human,
    )
    .await
}

#[cfg(test)]
mod tests {
    #[test]
    fn quality_gate_body_shape() {
        let body = serde_json::json!({"workspace_id": "ws-abc-0001"});
        assert_eq!(body["workspace_id"], "ws-abc-0001");
    }

    #[test]
    fn release_body_shape() {
        let body = serde_json::json!({"workspace_id": "ws-xyz-0042", "repo": "org/repo"});
        assert_eq!(body["workspace_id"], "ws-xyz-0042");
        assert_eq!(body["repo"], "org/repo");
    }

    #[test]
    fn workspace_list_filter_finds_active_wave() {
        let list = serde_json::json!({
            "workspaces": [
                {"workspace_id": "ws-old", "wave_db_id": 5, "status": "merged"},
                {"workspace_id": "ws-active", "wave_db_id": 5, "status": "active"},
                {"workspace_id": "ws-other", "wave_db_id": 9, "status": "active"},
            ]
        });
        let wave_id: i64 = 5;
        let found = list
            .get("workspaces")
            .and_then(|ws| ws.as_array())
            .and_then(|arr| {
                arr.iter().find(|w| {
                    w.get("wave_db_id")
                        .and_then(|v| v.as_i64())
                        .map_or(false, |id| id == wave_id)
                        && w.get("status")
                            .and_then(|v| v.as_str())
                            .map_or(true, |s| s == "active")
                })
            })
            .and_then(|w| w.get("workspace_id"))
            .and_then(|v| v.as_str())
            .map(str::to_owned);
        assert_eq!(found, Some("ws-active".to_string()));
    }
}
