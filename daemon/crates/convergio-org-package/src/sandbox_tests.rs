//! Tests for org sandbox enforcement.

use super::*;
use crate::manifest::{
    DelegationConfig, OrgManifest, PackageBudget, PackageMeta, PackagePermissions,
};

fn test_manifest() -> OrgManifest {
    OrgManifest {
        package: PackageMeta {
            name: "legal-corp".into(),
            version: "1.0.0".into(),
            description: "Legal compliance team".into(),
            author: "Convergio".into(),
            min_daemon_version: None,
            license: Some("MIT".into()),
        },
        permissions: PackagePermissions::default(),
        budget: PackageBudget {
            max_api_calls_per_hour: 100,
            max_tokens_per_day: 500_000,
            max_compute_seconds: 300,
        },
        delegation: DelegationConfig::default(),
        templates: Default::default(),
    }
}

#[test]
fn sandbox_prefixes_correct() {
    let sandbox = create_sandbox(&test_manifest());
    assert_eq!(sandbox.db_prefix, "org_legal_corp_");
    assert_eq!(sandbox.route_prefix, "/org/legal-corp");
    assert_eq!(sandbox.ipc_prefix, "org.legal-corp.");
}

#[test]
fn valid_db_table_passes() {
    let sandbox = create_sandbox(&test_manifest());
    check_db_table(&sandbox, "org_legal_corp_contracts").unwrap();
}

#[test]
fn invalid_db_table_rejected() {
    let sandbox = create_sandbox(&test_manifest());
    let err = check_db_table(&sandbox, "users").unwrap_err();
    assert!(err.to_string().contains("DB table violation"));
}

#[test]
fn valid_route_passes() {
    let sandbox = create_sandbox(&test_manifest());
    check_route(&sandbox, "/org/legal-corp/contracts").unwrap();
}

#[test]
fn invalid_route_rejected() {
    let sandbox = create_sandbox(&test_manifest());
    let err = check_route(&sandbox, "/api/admin/users").unwrap_err();
    assert!(err.to_string().contains("route violation"));
}

#[test]
fn valid_ipc_channel_passes() {
    let sandbox = create_sandbox(&test_manifest());
    check_ipc_channel(&sandbox, "org.legal-corp.review").unwrap();
}

#[test]
fn invalid_ipc_channel_rejected() {
    let sandbox = create_sandbox(&test_manifest());
    let err = check_ipc_channel(&sandbox, "global.broadcast").unwrap_err();
    assert!(err.to_string().contains("IPC channel violation"));
}

#[test]
fn budget_within_limit() {
    let sandbox = create_sandbox(&test_manifest());
    check_budget_limit(&sandbox, 50).unwrap();
}

#[test]
fn budget_exceeded() {
    let sandbox = create_sandbox(&test_manifest());
    let err = check_budget_limit(&sandbox, 100).unwrap_err();
    assert!(err.to_string().contains("exceeded"));
}

#[test]
fn prefix_migration_sql_transforms() {
    let sandbox = create_sandbox(&test_manifest());
    let sql = "CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY)";
    let prefixed = prefix_migration_sql(&sandbox, sql);
    assert!(prefixed.contains("org_legal_corp_contracts"));
}
