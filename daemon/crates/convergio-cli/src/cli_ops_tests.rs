// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_ops module (mesh and session commands).

use super::*;

#[test]
fn mesh_heartbeat_variant_exists() {
    let cmd = MeshCommands::Heartbeat {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, MeshCommands::Heartbeat { human: false, .. }));
}

#[test]
fn mesh_status_variant_exists() {
    let cmd = MeshCommands::Status {
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, MeshCommands::Status { human: true, .. }));
}

#[test]
fn mesh_cluster_status_variant_exists() {
    let cmd = MeshCommands::ClusterStatus {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, MeshCommands::ClusterStatus { .. }));
}

#[test]
fn session_reap_variant_exists() {
    let cmd = SessionCommands::Reap {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, SessionCommands::Reap { human: false, .. }));
}

#[test]
fn session_recovery_variant_exists() {
    let cmd = SessionCommands::Recovery {
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, SessionCommands::Recovery { human: true, .. }));
}

#[test]
fn mesh_heartbeat_url() {
    let url = format!("{}/api/heartbeat", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/heartbeat");
}

#[test]
fn mesh_status_url() {
    let url = format!("{}/api/mesh", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/mesh");
}

#[test]
fn mesh_cluster_status_url() {
    let url = format!("{}/api/heartbeat/status", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/heartbeat/status");
}

#[test]
fn session_reap_url() {
    let url = format!("{}/api/sessions/reap", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/sessions/reap");
}

#[test]
fn session_recovery_url() {
    let url = format!("{}/api/sessions/recovery", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/sessions/recovery");
}

#[test]
fn print_value_json_compact() {
    let val = serde_json::json!({"nodes": 3, "healthy": true});
    let compact = val.to_string();
    assert!(!compact.is_empty());
    assert!(!compact.contains('\n'));
}

#[test]
fn print_value_json_pretty() {
    let val = serde_json::json!({"nodes": 3});
    let pretty = serde_json::to_string_pretty(&val).unwrap();
    assert!(pretty.contains('\n'));
}

// --- Session Check ---

#[test]
fn session_check_variant_exists() {
    let cmd = SessionCommands::Check {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, SessionCommands::Check { human: false, .. }));
}

#[test]
fn session_check_url() {
    let url = format!("{}/api/dashboard", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/dashboard");
}

// --- Metrics ---

#[test]
fn metrics_summary_variant_exists() {
    let cmd = MetricsCommands::Summary {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, MetricsCommands::Summary { human: false, .. }));
}

#[test]
fn metrics_summary_url() {
    let url = format!("{}/api/metrics/summary", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/metrics/summary");
}

#[test]
fn metrics_collect_variant_exists() {
    let cmd = MetricsCommands::Collect {
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, MetricsCommands::Collect { human: true, .. }));
}

#[test]
fn metrics_collect_url() {
    let url = format!("{}/api/metrics/collect", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/metrics/collect");
}

// --- Alerts ---

#[test]
fn alert_list_variant_exists() {
    let cmd = AlertCommands::List {
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, AlertCommands::List { human: false, .. }));
}

#[test]
fn alert_list_url() {
    let url = format!("{}/api/notifications", "http://localhost:8420");
    assert_eq!(url, "http://localhost:8420/api/notifications");
}
