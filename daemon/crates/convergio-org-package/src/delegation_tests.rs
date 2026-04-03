//! Tests for inter-org delegation validation.

use super::*;
use crate::token::{OrgTokenBudget, OrgTokenClaims, OrgTokenPermissions};

fn source_claims() -> OrgTokenClaims {
    OrgTokenClaims {
        sub: "engineering-corp".into(),
        version: "1.0.0".into(),
        permissions: OrgTokenPermissions {
            ipc_publish: vec![],
            ipc_subscribe: vec![],
            routes: vec![],
            can_delegate: true,
            can_receive: false,
        },
        budget: OrgTokenBudget {
            max_api_calls_per_hour: 500,
            max_tokens_per_day: 5_000_000,
            max_compute_seconds: 1800,
        },
        iat: 1000,
        exp: 999_999,
    }
}

fn target_claims() -> OrgTokenClaims {
    OrgTokenClaims {
        sub: "legal-corp".into(),
        version: "1.0.0".into(),
        permissions: OrgTokenPermissions {
            ipc_publish: vec![],
            ipc_subscribe: vec![],
            routes: vec![],
            can_delegate: false,
            can_receive: true,
        },
        budget: OrgTokenBudget {
            max_api_calls_per_hour: 100,
            max_tokens_per_day: 1_000_000,
            max_compute_seconds: 600,
        },
        iat: 1000,
        exp: 999_999,
    }
}

fn make_request(budget: u64) -> DelegationRequest {
    DelegationRequest {
        from_org: "engineering-corp".into(),
        to_org: "legal-corp".into(),
        task: "Review contract compliance".into(),
        budget_tokens: budget,
        deadline: None,
    }
}

#[test]
fn valid_delegation_passes() {
    let req = make_request(500_000);
    let trusted = vec!["engineering-corp".to_string()];
    validate_delegation(&req, &source_claims(), &target_claims(), &trusted).unwrap();
}

#[test]
fn source_cannot_delegate_rejected() {
    let req = make_request(100_000);
    let mut src = source_claims();
    src.permissions.can_delegate = false;
    let trusted = vec!["engineering-corp".into()];
    let err = validate_delegation(&req, &src, &target_claims(), &trusted).unwrap_err();
    assert!(matches!(err, DelegationError::CannotDelegate(_)));
}

#[test]
fn target_cannot_receive_rejected() {
    let req = make_request(100_000);
    let mut tgt = target_claims();
    tgt.permissions.can_receive = false;
    let trusted = vec!["engineering-corp".into()];
    let err = validate_delegation(&req, &source_claims(), &tgt, &trusted).unwrap_err();
    assert!(matches!(err, DelegationError::CannotReceive(_)));
}

#[test]
fn untrusted_source_rejected() {
    let req = make_request(100_000);
    let trusted = vec!["other-org".to_string()];
    let err = validate_delegation(&req, &source_claims(), &target_claims(), &trusted).unwrap_err();
    assert!(matches!(err, DelegationError::NotTrusted(_, _)));
}

#[test]
fn wildcard_trust_allows_all() {
    let req = make_request(100_000);
    let trusted = vec!["*".to_string()];
    validate_delegation(&req, &source_claims(), &target_claims(), &trusted).unwrap();
}

#[test]
fn budget_exceeded_rejected() {
    let req = make_request(2_000_000); // exceeds target's 1M/day
    let trusted = vec!["engineering-corp".into()];
    let err = validate_delegation(&req, &source_claims(), &target_claims(), &trusted).unwrap_err();
    assert!(matches!(err, DelegationError::InsufficientBudget { .. }));
}

#[test]
fn create_delegation_returns_pending() {
    let req = make_request(100_000);
    let result = create_delegation(&req);
    assert_eq!(result.status, DelegationStatus::Pending);
    assert!(!result.id.is_empty());
}
