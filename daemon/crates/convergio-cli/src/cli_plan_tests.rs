// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_plan.rs — extracted for 250-line limit.

use super::*;

#[test]
fn plan_commands_list_variant_exists() {
    let cmd = PlanCommands::List {
        status: None,
        limit: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::List { .. }));
}

#[test]
fn plan_commands_list_with_status_filter() {
    let cmd = PlanCommands::List {
        status: Some("done".to_string()),
        limit: Some(10),
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::List { .. }));
}

#[test]
fn plan_commands_tree_variant_exists() {
    let cmd = PlanCommands::Tree {
        plan_id: 42,
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Tree { plan_id: 42, .. }));
}

#[test]
fn plan_commands_show_variant_exists() {
    let cmd = PlanCommands::Show {
        plan_id: 1,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Show { .. }));
}

#[test]
fn plan_commands_create_variant_exists() {
    let cmd = PlanCommands::Create {
        project_id: "convergio".to_string(),
        name: "Migration Plan".to_string(),
        source_file: Some("/tmp/spec.yaml".to_string()),
        parent: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Create { .. }));
}

#[test]
fn plan_commands_create_with_parent_variant_exists() {
    let cmd = PlanCommands::Create {
        project_id: "convergio".to_string(),
        name: "Sub Plan".to_string(),
        source_file: None,
        parent: Some(42),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Create { parent: Some(42), .. }));
}

#[test]
fn plan_commands_import_variant_exists() {
    let cmd = PlanCommands::Import {
        plan_id: 100,
        spec_file: "/tmp/spec.yaml".to_string(),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Import { plan_id: 100, .. }));
}

#[test]
fn plan_commands_readiness_variant_exists() {
    let cmd = PlanCommands::Readiness {
        plan_id: 688,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, PlanCommands::Readiness { plan_id: 688, .. }));
}
