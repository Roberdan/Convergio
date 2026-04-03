// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Setup wizard helper functions — network detection, API validation, env file.

use std::io;
use std::path::PathBuf;

// ---------------------------------------------------------------------------
// Node detection
// ---------------------------------------------------------------------------

/// Auto-detect short hostname for node name.
pub(crate) fn detect_hostname() -> String {
    hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown".to_string())
}

// ---------------------------------------------------------------------------
// Tailscale detection
// ---------------------------------------------------------------------------

pub(crate) struct TailscaleInfo {
    pub ip: String,
    pub peers: Vec<String>,
}

/// Check if Tailscale is installed and running. Returns IP + peer list.
pub(crate) fn detect_tailscale() -> Option<TailscaleInfo> {
    let output = std::process::Command::new("tailscale")
        .args(["status", "--json"])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).ok()?;
    let self_ip = json
        .get("Self")
        .and_then(|s| s.get("TailscaleIPs"))
        .and_then(|ips| ips.as_array())
        .and_then(|arr| arr.first())
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();
    let mut peers = Vec::new();
    if let Some(peer_map) = json.get("Peer").and_then(|p| p.as_object()) {
        for (_key, peer) in peer_map {
            if let Some(name) = peer.get("HostName").and_then(|h| h.as_str()) {
                let ip = peer
                    .get("TailscaleIPs")
                    .and_then(|ips| ips.as_array())
                    .and_then(|arr| arr.first())
                    .and_then(|v| v.as_str())
                    .unwrap_or("?");
                peers.push(format!("{name} ({ip})"));
            }
        }
    }
    Some(TailscaleInfo { ip: self_ip, peers })
}

// ---------------------------------------------------------------------------
// LAN interface detection
// ---------------------------------------------------------------------------

/// List non-loopback network interface names (macOS/Linux).
pub(crate) fn detect_lan_interfaces() -> Vec<String> {
    let output = std::process::Command::new("ifconfig")
        .output()
        .or_else(|_| std::process::Command::new("ip").args(["link"]).output());
    let Ok(output) = output else {
        return Vec::new();
    };
    let text = String::from_utf8_lossy(&output.stdout);
    let mut ifaces = Vec::new();
    for line in text.lines() {
        // macOS: "en0: flags=..." / Linux: "2: eth0: <..."
        if let Some(name) = extract_iface_name(line) {
            if name != "lo" && name != "lo0" {
                ifaces.push(name);
            }
        }
    }
    ifaces.dedup();
    ifaces
}

fn extract_iface_name(line: &str) -> Option<String> {
    // macOS format: "en0: flags=8863<UP,..."
    if !line.starts_with(' ') && !line.starts_with('\t') {
        if let Some(name) = line.split(':').next() {
            let name = name.trim();
            // Linux ip link: "2: eth0" — strip leading number
            let name = if let Some((_num, rest)) = name.split_once(": ") {
                rest
            } else {
                name
            };
            if !name.is_empty()
                && name
                    .chars()
                    .all(|c| c.is_alphanumeric() || c == '-' || c == '_')
            {
                return Some(name.to_string());
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// API key validation
// ---------------------------------------------------------------------------

/// Test Anthropic API key with a minimal models endpoint call.
pub(crate) async fn validate_api_key(key: &str) -> bool {
    let client = reqwest::Client::new();
    let resp = client
        .get("https://api.anthropic.com/v1/models")
        .header("x-api-key", key)
        .header("anthropic-version", "2023-06-01")
        .send()
        .await;
    matches!(resp, Ok(r) if r.status().is_success())
}

// ---------------------------------------------------------------------------
// Env file management
// ---------------------------------------------------------------------------

fn env_file_path() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".convergio/env")
}

/// Append or update ANTHROPIC_API_KEY in ~/.convergio/env.
pub(crate) fn write_env_file(api_key: &str) -> io::Result<()> {
    let path = env_file_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let existing = std::fs::read_to_string(&path).unwrap_or_default();
    let mut lines: Vec<String> = existing
        .lines()
        .filter(|l| !l.starts_with("ANTHROPIC_API_KEY="))
        .map(|l| l.to_string())
        .collect();
    lines.push(format!("ANTHROPIC_API_KEY={api_key}"));
    std::fs::write(&path, lines.join("\n") + "\n")
}

// ---------------------------------------------------------------------------
// Config serialization — write a populated config.toml
// ---------------------------------------------------------------------------

/// Generate config.toml content from wizard answers.
pub(crate) fn render_config(node_name: &str, role: &str, use_tailscale: bool) -> String {
    let transport = if use_tailscale { "tailscale" } else { "lan" };
    let discovery = if use_tailscale { "tailscale" } else { "mdns" };
    format!(
        r#"# Convergio Platform Configuration
# Generated by `cvg setup`

[node]
name = "{node_name}"
role = "{role}"

[daemon]
port = 8420
auto_update = true

[mesh]
transport = "{transport}"
discovery = "{discovery}"

[mesh.tailscale]
enabled = {use_tailscale}

[inference]
default_model = "claude-sonnet-4-6"
api_key_env = "ANTHROPIC_API_KEY"

[kernel]
model = "none"
max_tokens = 2048

[telegram]
enabled = false
"#
    )
}
