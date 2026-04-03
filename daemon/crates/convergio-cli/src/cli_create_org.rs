// CLI handlers for creating orgs — delegates to daemon HTTP API.
// Original used convergio_core::org directly; now pure HTTP client.

use crate::cli_error::CliError;

/// Create an org from a mission statement via daemon API.
pub async fn handle_create_org(
    name: &str,
    mission: &str,
    budget: f64,
    yes: bool,
    api_url: &str,
) -> Result<(), CliError> {
    let body = serde_json::json!({
        "name": name,
        "mission": mission,
        "budget": budget,
        "auto_confirm": yes,
    });
    let url = format!("{api_url}/api/orgs/create-from-mission");
    let val = crate::cli_http::post_and_return(&url, &body)
        .await
        .map_err(|code| CliError::ApiCallFailed(format!("daemon error (code {code})")))?;
    println!(
        "{}",
        serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
    );
    Ok(())
}

/// Create an org from a scanned repo via daemon API.
pub async fn handle_create_org_from(
    path: &str,
    name: Option<&str>,
    budget: f64,
    yes: bool,
    api_url: &str,
) -> Result<(), CliError> {
    let body = serde_json::json!({
        "path": path,
        "name": name,
        "budget": budget,
        "auto_confirm": yes,
    });
    let url = format!("{api_url}/api/orgs/create-from-repo");
    let val = crate::cli_http::post_and_return(&url, &body)
        .await
        .map_err(|code| CliError::ApiCallFailed(format!("daemon error (code {code})")))?;
    println!(
        "{}",
        serde_json::to_string_pretty(&val).unwrap_or_else(|_| val.to_string())
    );
    Ok(())
}
