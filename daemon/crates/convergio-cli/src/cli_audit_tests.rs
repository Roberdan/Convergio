// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tests for cli_audit — split to keep cli_audit.rs under 250 lines.

use super::*;
use std::fs;
use tempfile::TempDir;

fn make_tmp() -> TempDir {
    tempfile::tempdir().expect("tempdir")
}

fn write_constitution(dir: &TempDir) {
    for f in CONSTITUTION_FILES {
        fs::write(dir.path().join(f), b"x").unwrap();
    }
}

// --- Constitution checks ---

#[test]
fn constitution_all_present_no_violation() {
    let dir = make_tmp();
    write_constitution(&dir);
    let violations = audit(dir.path());
    let count = violations
        .iter()
        .filter(|v| matches!(v.kind, ViolationKind::ConstitutionMissing { .. }))
        .count();
    assert_eq!(count, 0, "all constitution files present");
}

#[test]
fn constitution_missing_one_raises_violation() {
    let dir = make_tmp();
    for f in CONSTITUTION_FILES.iter().skip(1) {
        fs::write(dir.path().join(f), b"x").unwrap();
    }
    let violations = audit(dir.path());
    let missing: Vec<_> = violations.iter()
        .filter(|v| matches!(&v.kind, ViolationKind::ConstitutionMissing { filename } if filename == "CONSTITUTION.md"))
        .collect();
    assert_eq!(missing.len(), 1, "CONSTITUTION.md missing raises violation");
}

// --- Line count checks ---

#[test]
fn file_under_250_lines_passes() {
    let dir = make_tmp();
    write_constitution(&dir);
    let content = "// Copyright (c) 2026 Roberto D'Angelo.\nfn x() {}\n".repeat(100);
    fs::write(dir.path().join("ok.rs"), content.as_bytes()).unwrap();
    let line_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::TooManyLines { .. }))
        .collect();
    assert!(line_viol.is_empty());
}

#[test]
fn file_over_250_lines_fails() {
    let dir = make_tmp();
    write_constitution(&dir);
    let mut content = "// Copyright (c) 2026 Roberto D'Angelo.\n".to_string();
    for i in 0..260 {
        content.push_str(&format!("let x{i} = {i};\n"));
    }
    fs::write(dir.path().join("big.rs"), content.as_bytes()).unwrap();
    let line_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::TooManyLines { .. }))
        .collect();
    assert_eq!(line_viol.len(), 1);
    if let ViolationKind::TooManyLines { lines } = &line_viol[0].kind {
        assert!(*lines > 250);
    }
}

// --- Copyright checks ---

#[test]
fn file_with_copyright_passes() {
    let dir = make_tmp();
    write_constitution(&dir);
    fs::write(
        dir.path().join("ok.rs"),
        b"// Copyright (c) 2026 Roberto D'Angelo.\nfn x() {}",
    )
    .unwrap();
    let copy_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::MissingCopyright))
        .collect();
    assert!(copy_viol.is_empty());
}

#[test]
fn file_without_copyright_fails() {
    let dir = make_tmp();
    write_constitution(&dir);
    fs::write(dir.path().join("bad.rs"), b"fn main() {}\n").unwrap();
    let copy_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::MissingCopyright))
        .filter(|v| v.path.file_name().map(|n| n == "bad.rs").unwrap_or(false))
        .collect();
    assert_eq!(copy_viol.len(), 1);
}

// --- Token budget checks ---

#[test]
fn rules_file_within_budget_passes() {
    let dir = make_tmp();
    write_constitution(&dir);
    let rules = dir.path().join("rules");
    fs::create_dir(&rules).unwrap();
    fs::write(rules.join("test.md"), b"# small rule").unwrap();
    let budget_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::TokenBudgetExceeded { .. }))
        .collect();
    assert!(budget_viol.is_empty());
}

#[test]
fn rules_file_over_budget_fails() {
    let dir = make_tmp();
    write_constitution(&dir);
    let rules = dir.path().join("rules");
    fs::create_dir(&rules).unwrap();
    // 8193 bytes > 8192 byte limit for rules/*.md
    fs::write(rules.join("oversize.md"), vec![b'x'; 8_193]).unwrap();
    let budget_viol: Vec<_> = audit(dir.path())
        .into_iter()
        .filter(|v| matches!(v.kind, ViolationKind::TokenBudgetExceeded { .. }))
        .filter(|v| {
            v.path
                .file_name()
                .map(|n| n == "oversize.md")
                .unwrap_or(false)
        })
        .collect();
    assert_eq!(budget_viol.len(), 1);
}

// --- format_violation ---

#[test]
fn format_violation_lines() {
    let v = Violation {
        path: PathBuf::from("src/big.rs"),
        kind: ViolationKind::TooManyLines { lines: 300 },
    };
    let s = format_violation(&v);
    assert!(s.contains("300") && s.contains("LINES"));
}

#[test]
fn format_violation_copyright() {
    let v = Violation {
        path: PathBuf::from("src/bad.rs"),
        kind: ViolationKind::MissingCopyright,
    };
    assert!(format_violation(&v).contains("COPYRIGHT"));
}

#[test]
fn format_violation_constitution() {
    let v = Violation {
        path: PathBuf::from("CONSTITUTION.md"),
        kind: ViolationKind::ConstitutionMissing {
            filename: "CONSTITUTION.md".into(),
        },
    };
    assert!(format_violation(&v).contains("CONSTITUTION"));
}

#[test]
fn format_violation_token_budget() {
    let v = Violation {
        path: PathBuf::from("rules/big.md"),
        kind: ViolationKind::TokenBudgetExceeded {
            bytes: 9000,
            max_bytes: 8192,
            label: "rules/*.md".into(),
        },
    };
    let s = format_violation(&v);
    assert!(s.contains("TOKEN-BUDGET") && s.contains("9000"));
}
