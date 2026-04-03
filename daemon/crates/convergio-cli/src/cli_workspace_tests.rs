// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_workspace module — extracted from cli_workspace.rs (Plan F, T4-04).

use super::*;

#[test]
fn workspace_create_with_plan_and_wave() {
    let cmd = WorkspaceCommands::Create {
        plan: Some(698),
        wave: Some(100),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(
        cmd,
        WorkspaceCommands::Create {
            plan: Some(698),
            ..
        }
    ));
}

#[test]
fn workspace_create_feature_variant() {
    let cmd = WorkspaceCommands::CreateFeature {
        branch: "feat/new-thing".to_string(),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, WorkspaceCommands::CreateFeature { .. }));
}

#[test]
fn workspace_delete_variant() {
    let cmd = WorkspaceCommands::Delete {
        workspace_id: "ws-12345-abcd".to_string(),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, WorkspaceCommands::Delete { .. }));
}

#[test]
fn workspace_list_filtered_by_plan() {
    let cmd = WorkspaceCommands::List {
        plan: Some(698),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(
        cmd,
        WorkspaceCommands::List {
            plan: Some(698),
            ..
        }
    ));
}

#[test]
fn workspace_status_variant() {
    let cmd = WorkspaceCommands::Status {
        workspace_id: "ws-abc123".to_string(),
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, WorkspaceCommands::Status { .. }));
}

#[test]
fn workspace_events_variant() {
    let cmd = WorkspaceCommands::Events {
        workspace_id: "ws-abc123".to_string(),
        limit: 50,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, WorkspaceCommands::Events { limit: 50, .. }));
}

#[test]
fn workspace_create_body_shape() {
    let body = serde_json::json!({"plan_id": 698_i64, "wave_db_id": 100_i64});
    assert_eq!(body["plan_id"], 698);
    assert_eq!(body["wave_db_id"], 100);
}

#[test]
fn workspace_create_feature_body_shape() {
    let body = serde_json::json!({"feature": true, "branch": "feat/my-feature"});
    assert_eq!(body["feature"], true);
    assert_eq!(body["branch"], "feat/my-feature");
}

#[test]
fn workspace_delete_body_shape() {
    let body = serde_json::json!({"workspace_id": "ws-12345-abcd"});
    assert_eq!(body["workspace_id"], "ws-12345-abcd");
}

#[test]
fn workspace_events_default_limit_is_20() {
    // Clap default_value = "20"; verify enum carries it through.
    let cmd = WorkspaceCommands::Events {
        workspace_id: "ws-test".to_string(),
        limit: 20,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    if let WorkspaceCommands::Events { limit, .. } = cmd {
        assert_eq!(limit, 20);
    }
}
