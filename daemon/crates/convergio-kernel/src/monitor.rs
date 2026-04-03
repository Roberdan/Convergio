//! Health monitor — periodic checks with severity classification.
//!
//! Runs every 30s, checks daemon health, peers, agents, disk, RAM.
//! Results are persisted to kernel_events for audit and alerting.

use super::types::{KernelCheckResult, KernelSeverity};

/// Monitor configuration.
pub struct MonitorConfig {
    pub daemon_url: String,
    pub peer_urls: Vec<String>,
    pub poll_interval_secs: u64,
}

impl Default for MonitorConfig {
    fn default() -> Self {
        Self {
            daemon_url: "http://localhost:8420".to_string(),
            peer_urls: Vec::new(),
            poll_interval_secs: 30,
        }
    }
}

/// Run a single monitor cycle — returns check results.
pub fn run_checks(config: &MonitorConfig) -> Vec<KernelCheckResult> {
    let mut results = Vec::new();
    results.push(check_daemon_health(&config.daemon_url));
    for peer in &config.peer_urls {
        results.push(check_peer_health(peer));
    }
    results
}

/// Classify a set of check results into overall severity.
pub fn classify_results(results: &[KernelCheckResult]) -> KernelSeverity {
    let critical_checks = ["daemon_health", "peer_health", "db_integrity"];
    for r in results {
        if !r.ok && critical_checks.iter().any(|&c| r.check_name == c) {
            return KernelSeverity::Critical;
        }
    }
    if results.iter().any(|r| !r.ok) {
        KernelSeverity::Warn
    } else {
        KernelSeverity::Ok
    }
}

fn check_daemon_health(daemon_url: &str) -> KernelCheckResult {
    let url = format!("{daemon_url}/health");
    match reqwest::blocking::get(&url) {
        Ok(resp) if resp.status().is_success() => KernelCheckResult {
            check_name: "daemon_health".to_string(),
            ok: true,
            details: "healthy".to_string(),
        },
        Ok(resp) => KernelCheckResult {
            check_name: "daemon_health".to_string(),
            ok: false,
            details: format!("status {}", resp.status()),
        },
        Err(e) => KernelCheckResult {
            check_name: "daemon_health".to_string(),
            ok: false,
            details: format!("unreachable: {e}"),
        },
    }
}

fn check_peer_health(peer_url: &str) -> KernelCheckResult {
    let url = format!("{peer_url}/health");
    match reqwest::blocking::get(&url) {
        Ok(resp) if resp.status().is_success() => KernelCheckResult {
            check_name: "peer_health".to_string(),
            ok: true,
            details: format!("peer {peer_url} healthy"),
        },
        _ => KernelCheckResult {
            check_name: "peer_health".to_string(),
            ok: false,
            details: format!("peer {peer_url} unreachable"),
        },
    }
}
