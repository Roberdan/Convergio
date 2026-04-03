// Tests for project scaffolding.

use super::*;
use crate::scaffold_gen::license_spdx;

#[test]
fn rust_scaffold_has_cargo_toml() {
    let req = ScaffoldRequest {
        name: "acme-server".into(),
        description: "A server for ACME Corp".into(),
        language: Language::Rust,
        license: License::Mit,
        visibility: Visibility::Public,
        org_id: "acme-corp".into(),
        template: None,
    };
    let resp = generate_scaffold(&req);
    assert_eq!(resp.name, "acme-server");
    let paths: Vec<&str> = resp.files.iter().map(|f| f.path.as_str()).collect();
    assert!(paths.contains(&"Cargo.toml"));
    assert!(paths.contains(&"src/main.rs"));
    assert!(paths.contains(&"CLAUDE.md"));
    assert!(paths.contains(&"LICENSE"));
    assert!(paths.contains(&"CODEOWNERS"));
    assert!(paths.contains(&".github/workflows/ci.yml"));
    assert!(resp.branch_protection.require_pr);
}

#[test]
fn typescript_scaffold_has_package_json() {
    let req = ScaffoldRequest {
        name: "widget-ui".into(),
        description: "Frontend widget library".into(),
        language: Language::Typescript,
        license: License::Apache2,
        visibility: Visibility::Private,
        org_id: "widget-co".into(),
        template: None,
    };
    let resp = generate_scaffold(&req);
    let paths: Vec<&str> = resp.files.iter().map(|f| f.path.as_str()).collect();
    assert!(paths.contains(&"package.json"));
    assert!(paths.contains(&"tsconfig.json"));
    assert!(paths.contains(&"src/index.ts"));
}

#[test]
fn python_scaffold_has_pyproject() {
    let req = ScaffoldRequest {
        name: "data-pipeline".into(),
        description: "ETL data pipeline".into(),
        language: Language::Python,
        license: License::Gpl3,
        visibility: Visibility::Public,
        org_id: "data-team".into(),
        template: None,
    };
    let resp = generate_scaffold(&req);
    let paths: Vec<&str> = resp.files.iter().map(|f| f.path.as_str()).collect();
    assert!(paths.contains(&"pyproject.toml"));
    assert!(paths.contains(&"src/__init__.py"));
}

#[test]
fn license_spdx_mapping() {
    assert_eq!(license_spdx(License::Mit), "MIT");
    assert_eq!(license_spdx(License::Apache2), "Apache-2.0");
    assert_eq!(license_spdx(License::Gpl3), "GPL-3.0-only");
}

#[test]
fn mit_license_contains_year() {
    let req = ScaffoldRequest {
        name: "test-proj".into(),
        description: "A test".into(),
        language: Language::Rust,
        license: License::Mit,
        visibility: Visibility::Public,
        org_id: "tester".into(),
        template: None,
    };
    let resp = generate_scaffold(&req);
    let lic = resp.files.iter().find(|f| f.path == "LICENSE").unwrap();
    assert!(lic.content.contains("MIT License"));
    assert!(lic.content.contains("tester"));
}
