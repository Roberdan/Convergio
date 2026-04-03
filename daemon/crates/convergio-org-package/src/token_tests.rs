//! Tests for scoped org tokens.

use super::*;

fn test_claims() -> OrgTokenClaims {
    create_org_claims(
        "legal-corp",
        "1.0.0",
        OrgTokenPermissions {
            ipc_publish: vec!["legal.review".into(), "legal.complete".into()],
            ipc_subscribe: vec!["tasks.assigned".into()],
            routes: vec!["/api/legal".into()],
            can_delegate: true,
            can_receive: true,
        },
        OrgTokenBudget {
            max_api_calls_per_hour: 100,
            max_tokens_per_day: 500_000,
            max_compute_seconds: 300,
        },
        3600,
    )
}

#[test]
fn create_claims_sets_expiry() {
    let claims = test_claims();
    assert_eq!(claims.sub, "legal-corp");
    assert!(claims.exp > claims.iat);
    assert_eq!(claims.exp - claims.iat, 3600);
}

#[test]
fn valid_token_passes_expiry() {
    let claims = test_claims();
    validate_expiry(&claims).unwrap();
}

#[test]
fn expired_token_rejected() {
    let mut claims = test_claims();
    claims.exp = 0; // epoch = definitely expired
    let err = validate_expiry(&claims).unwrap_err();
    assert!(err.to_string().contains("expired"));
}

#[test]
fn allowed_ipc_publish_passes() {
    let claims = test_claims();
    check_ipc_publish(&claims, "legal.review").unwrap();
    check_ipc_publish(&claims, "legal.complete").unwrap();
}

#[test]
fn disallowed_ipc_publish_rejected() {
    let claims = test_claims();
    let err = check_ipc_publish(&claims, "finance.report").unwrap_err();
    assert!(err.to_string().contains("cannot publish"));
}

#[test]
fn allowed_ipc_subscribe_passes() {
    let claims = test_claims();
    check_ipc_subscribe(&claims, "tasks.assigned").unwrap();
}

#[test]
fn disallowed_ipc_subscribe_rejected() {
    let claims = test_claims();
    let err = check_ipc_subscribe(&claims, "secret.channel").unwrap_err();
    assert!(err.to_string().contains("cannot subscribe"));
}

#[test]
fn budget_within_limit_passes() {
    let claims = test_claims();
    check_budget(&claims, 50).unwrap();
}

#[test]
fn budget_exceeded_rejected() {
    let claims = test_claims();
    let err = check_budget(&claims, 100).unwrap_err();
    assert!(err.to_string().contains("exceeded"));
}

#[test]
fn wildcard_ipc_publish_allows_all() {
    let claims = create_org_claims(
        "admin-org",
        "1.0.0",
        OrgTokenPermissions {
            ipc_publish: vec!["*".into()],
            ipc_subscribe: vec![],
            routes: vec![],
            can_delegate: false,
            can_receive: false,
        },
        OrgTokenBudget {
            max_api_calls_per_hour: 1000,
            max_tokens_per_day: 10_000_000,
            max_compute_seconds: 3600,
        },
        86400,
    );
    check_ipc_publish(&claims, "anything.at.all").unwrap();
}
