//! Tests for org package manifest parsing and validation.

use super::*;

fn valid_toml() -> String {
    r#"
[package]
name = "legal-corp"
version = "1.0.0"
description = "Legal compliance organization"
author = "Convergio"
license = "MIT"

[permissions]
ipc_publish = ["legal.review"]
ipc_subscribe = ["tasks.assigned"]
routes = ["/api/legal"]
allow_subprocess = false

[budget]
max_api_calls_per_hour = 200
max_tokens_per_day = 1000000
max_compute_seconds = 600

[delegation]
can_delegate = true
can_receive = true
trusted_orgs = ["engineering-corp"]
"#
    .to_string()
}

#[test]
fn parse_valid_manifest() {
    let m = parse_manifest(&valid_toml()).unwrap();
    assert_eq!(m.package.name, "legal-corp");
    assert_eq!(m.package.version, "1.0.0");
    assert!(m.delegation.can_delegate);
    assert_eq!(m.delegation.trusted_orgs, vec!["engineering-corp"]);
    assert_eq!(m.budget.max_api_calls_per_hour, 200);
}

#[test]
fn missing_name_rejected() {
    let toml = r#"
[package]
name = ""
version = "1.0.0"
description = "test"
author = "test"
"#;
    let err = parse_manifest(toml).unwrap_err();
    assert!(err.to_string().contains("missing required field"));
}

#[test]
fn invalid_version_rejected() {
    let toml = r#"
[package]
name = "test-org"
version = "1.0"
description = "test"
author = "test"
"#;
    let err = parse_manifest(toml).unwrap_err();
    assert!(err.to_string().contains("invalid version"));
}

#[test]
fn name_with_spaces_rejected() {
    let toml = r#"
[package]
name = "bad name"
version = "1.0.0"
description = "test"
author = "test"
"#;
    let err = parse_manifest(toml).unwrap_err();
    assert!(err.to_string().contains("invalid name"));
}

#[test]
fn name_too_long_rejected() {
    let long_name = "a".repeat(65);
    let toml = format!(
        r#"
[package]
name = "{long_name}"
version = "1.0.0"
description = "test"
author = "test"
"#
    );
    let err = parse_manifest(&toml).unwrap_err();
    assert!(err.to_string().contains("too long"));
}

#[test]
fn defaults_applied_for_optional_sections() {
    let toml = r#"
[package]
name = "minimal-org"
version = "0.1.0"
description = "minimal"
author = "test"
"#;
    let m = parse_manifest(toml).unwrap();
    assert!(!m.delegation.can_delegate);
    assert!(!m.delegation.can_receive);
    assert!(m.permissions.ipc_publish.is_empty());
    assert_eq!(m.budget.max_api_calls_per_hour, 500);
}
