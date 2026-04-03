//! HTTP bridge to the Convergio daemon API.
//!
//! Each MCP tool handler calls the daemon over HTTP.
//! Uses reqwest::blocking with a 5-second timeout.

use serde_json::Value;
use std::time::Duration;

use crate::ring::McpError;

// ── Client ───────────────────────────────────────────────────────────────────

fn make_client() -> reqwest::blocking::Client {
    reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .unwrap_or_else(|_| reqwest::blocking::Client::new())
}

/// GET request to daemon, returning parsed JSON.
pub fn http_get(url: &str, token: Option<&str>) -> Result<Value, McpError> {
    let client = make_client();
    let mut req = client.get(url);
    if let Some(t) = token {
        req = req.bearer_auth(t);
    }
    let resp = req.send().map_err(|_| McpError::DaemonUnreachable)?;
    if !resp.status().is_success() {
        return Err(McpError::DaemonError(format!(
            "HTTP {}",
            resp.status().as_u16()
        )));
    }
    resp.json::<Value>()
        .map_err(|e| McpError::DaemonError(e.to_string()))
}

/// POST request to daemon with JSON body, returning parsed JSON.
pub fn http_post(url: &str, token: Option<&str>, body: &Value) -> Result<Value, McpError> {
    let client = make_client();
    let mut req = client.post(url).json(body);
    if let Some(t) = token {
        req = req.bearer_auth(t);
    }
    let resp = req.send().map_err(|_| McpError::DaemonUnreachable)?;
    if !resp.status().is_success() {
        return Err(McpError::DaemonError(format!(
            "HTTP {}",
            resp.status().as_u16()
        )));
    }
    resp.json::<Value>()
        .map_err(|e| McpError::DaemonError(e.to_string()))
}
