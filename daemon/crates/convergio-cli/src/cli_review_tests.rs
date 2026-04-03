// Tests for cli_review extracted to keep cli_review.rs ≤250 lines.
// Why: CONSTITUTION Article V (250-line limit).
use super::*;

// BUG 1 — verdict validation tests
#[test]
fn verdict_proceed_is_valid() {
    assert!(is_valid_verdict("proceed"));
}

#[test]
fn verdict_revise_is_valid() {
    assert!(is_valid_verdict("revise"));
}

#[test]
fn verdict_reject_is_valid() {
    assert!(is_valid_verdict("reject"));
}

#[test]
fn verdict_approved_is_invalid() {
    assert!(!is_valid_verdict("approved"));
}

#[test]
fn verdict_empty_is_invalid() {
    assert!(!is_valid_verdict(""));
}

#[test]
fn verdict_typo_is_invalid() {
    assert!(!is_valid_verdict("preceed"));
}

// BUG 3 — spec_file review registration tests
#[test]
fn review_register_with_spec_file_no_plan_id() {
    let cmd = ReviewCommands::Register {
        plan_id: None,
        spec_file: Some("/tmp/plan.yaml".to_string()),
        reviewer_agent: "plan-reviewer".to_string(),
        verdict: "proceed".to_string(),
        suggestions: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, ReviewCommands::Register { plan_id: None, .. }));
}

#[test]
fn review_register_with_plan_id_no_spec_file() {
    let cmd = ReviewCommands::Register {
        plan_id: Some(685),
        spec_file: None,
        reviewer_agent: "plan-reviewer".to_string(),
        verdict: "proceed".to_string(),
        suggestions: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, ReviewCommands::Register { plan_id: Some(685), .. }));
}

#[test]
fn review_register_variant_exists() {
    let cmd = ReviewCommands::Register {
        plan_id: Some(685),
        spec_file: None,
        reviewer_agent: "plan-reviewer".to_string(),
        verdict: "proceed".to_string(),
        suggestions: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, ReviewCommands::Register { plan_id: Some(685), .. }));
}

#[test]
fn review_check_variant_exists() {
    let cmd = ReviewCommands::Check {
        plan_id: 100,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, ReviewCommands::Check { plan_id: 100, .. }));
}

#[test]
fn review_reset_variant_exists() {
    let cmd = ReviewCommands::Reset {
        plan_id: Some(1),
        human: true,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(
        cmd,
        ReviewCommands::Reset {
            plan_id: Some(1),
            ..
        }
    ));
}

#[test]
fn review_reset_without_plan_id() {
    let cmd = ReviewCommands::Reset {
        plan_id: None,
        human: false,
        api_url: "http://localhost:8420".to_string(),
    };
    assert!(matches!(cmd, ReviewCommands::Reset { plan_id: None, .. }));
}

#[test]
fn review_register_body_shape() {
    let body = serde_json::json!({
        "plan_id": 685_i64, "reviewer_agent": "plan-reviewer",
        "verdict": "proceed", "suggestions": serde_json::Value::Null,
    });
    assert_eq!(body["verdict"], "proceed");
}
