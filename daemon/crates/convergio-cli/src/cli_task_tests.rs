use super::*;

#[test]
fn task_commands_update_variant_exists() {
    let cmd = TaskCommands::Update {
        task_id: 100,
        status: "done".to_string(),
        summary: Some("finished".to_string()),
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, TaskCommands::Update { task_id: 100, .. }));
}

#[test]
fn task_commands_validate_variant_exists() {
    let cmd = TaskCommands::Validate {
        task_id: 1,
        plan_id: 685,
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, TaskCommands::Validate { plan_id: 685, .. }));
}

#[test]
fn task_commands_kb_search_variant_exists() {
    let cmd = TaskCommands::KbSearch {
        query: "test".to_string(),
        limit: 5,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, TaskCommands::KbSearch { .. }));
}

#[test]
fn task_commands_approve_variant_exists() {
    let cmd = TaskCommands::Approve {
        task_id: 50,
        comment: Some("looks good".to_string()),
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, TaskCommands::Approve { task_id: 50, .. }));
}

#[test]
fn print_value_json_compact() {
    let val = serde_json::json!({"ok": true, "data": [1, 2]});
    let compact = val.to_string();
    assert!(!compact.is_empty());
}

#[test]
fn print_value_json_pretty() {
    let val = serde_json::json!({"ok": true});
    let pretty = serde_json::to_string_pretty(&val).unwrap();
    assert!(pretty.contains('\n'));
}

#[test]
fn mechanical_human_output_handles_approved() {
    let val = serde_json::json!({
        "ok": true,
        "mechanical": {
            "status": "APPROVED",
            "phase": "mechanical",
            "gates": [
                {"gate": "status_check", "passed": true, "details": []},
                {"gate": "test_criteria", "passed": true, "details": []},
            ],
            "thor_invoked": false,
            "note": "mechanical gates passed, Thor validation at wave level"
        }
    });
    print_mechanical_human(&val);
}

#[test]
fn mechanical_human_output_handles_rejected() {
    let val = serde_json::json!({
        "ok": false,
        "mechanical": {
            "status": "REJECTED",
            "phase": "mechanical",
            "gates": [
                {"gate": "status_check", "passed": false, "details": ["status is 'pending', expected 'submitted'"]},
            ],
            "thor_invoked": false,
            "note": "mechanical gates failed"
        }
    });
    print_mechanical_human(&val);
}

#[test]
fn mechanical_human_output_handles_missing_mechanical() {
    let val = serde_json::json!({"ok": true});
    print_mechanical_human(&val);
}
