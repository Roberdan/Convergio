// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Audit CLI — replaces project-audit.sh.
// Checks: file sizes (>250 lines), token budget, copyright headers, constitution files.

use std::path::{Path, PathBuf};

/// Constitution files that must exist at the project root.
pub const CONSTITUTION_FILES: &[&str] = &[
    "CONSTITUTION.md",
    "AgenticManifesto.md",
    "LEGAL_NOTICE.md",
    "CLAUDE.md",
];

/// Token budget limits (in bytes) per instruction file type.
/// Mirrors claude-config/rules/token-budget.md.
pub struct Budget {
    pub pattern: &'static str,
    pub max_bytes: u64,
    pub label: &'static str,
}

pub const BUDGETS: &[Budget] = &[
    Budget {
        pattern: "CLAUDE.md",
        max_bytes: 16_384,
        label: "CLAUDE.md/AGENTS.md",
    },
    Budget {
        pattern: "AGENTS.md",
        max_bytes: 16_384,
        label: "CLAUDE.md/AGENTS.md",
    },
    Budget {
        pattern: "rules/",
        max_bytes: 8_192,
        label: "rules/*.md",
    },
    Budget {
        pattern: "skills/",
        max_bytes: 6_144,
        label: "skills/*/*.md",
    },
    Budget {
        pattern: "agents/",
        max_bytes: 6_144,
        label: "agents/*/*.md",
    },
    Budget {
        pattern: "copilot-agents/",
        max_bytes: 6_144,
        label: "copilot-agents/*.md",
    },
];

#[derive(Debug)]
pub struct Violation {
    pub path: PathBuf,
    pub kind: ViolationKind,
}

#[derive(Debug, PartialEq)]
pub enum ViolationKind {
    /// Source file exceeds 250-line limit.
    TooManyLines { lines: usize },
    /// Instruction file exceeds token budget.
    TokenBudgetExceeded {
        bytes: u64,
        max_bytes: u64,
        label: String,
    },
    /// Source file is missing the required copyright header.
    MissingCopyright,
    /// A required constitution file is absent from the project root.
    ConstitutionMissing { filename: String },
}

/// Run all audit checks under `root`.  Returns list of violations (empty = clean).
pub fn audit(root: &Path) -> Vec<Violation> {
    let mut violations = Vec::new();
    check_constitution(root, &mut violations);
    walk(root, root, &mut violations);
    violations
}

/// Verify that all required constitution files exist at the project root.
fn check_constitution(root: &Path, out: &mut Vec<Violation>) {
    for name in CONSTITUTION_FILES {
        if !root.join(name).exists() {
            out.push(Violation {
                path: root.join(name),
                kind: ViolationKind::ConstitutionMissing {
                    filename: name.to_string(),
                },
            });
        }
    }
}

/// Recursively walk the directory tree, skipping hidden dirs and build artifacts.
fn walk(root: &Path, dir: &Path, out: &mut Vec<Violation>) {
    let entries = match std::fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let name = entry.file_name();
        let name_str = name.to_string_lossy();
        // Skip hidden dirs and common build/generated dirs.
        if name_str.starts_with('.')
            || matches!(
                name_str.as_ref(),
                "target" | "node_modules" | "dist" | "__pycache__"
            )
        {
            continue;
        }
        if path.is_dir() {
            walk(root, &path, out);
        } else if path.is_file() {
            check_file(root, &path, out);
        }
    }
}

/// Apply all file-level checks.
fn check_file(root: &Path, path: &Path, out: &mut Vec<Violation>) {
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
    // Source files: line count + copyright.
    if matches!(ext, "rs" | "ts" | "js" | "py" | "sh") {
        if let Ok(content) = std::fs::read_to_string(path) {
            let lines = content.lines().count();
            if lines > 250 {
                out.push(Violation {
                    path: path.to_owned(),
                    kind: ViolationKind::TooManyLines { lines },
                });
            }
            if !has_copyright(&content) {
                out.push(Violation {
                    path: path.to_owned(),
                    kind: ViolationKind::MissingCopyright,
                });
            }
        }
        return;
    }
    // Instruction Markdown files: token budget check.
    if ext == "md" {
        if let Some(budget) = find_budget(root, path) {
            if let Ok(meta) = std::fs::metadata(path) {
                if meta.len() > budget.max_bytes {
                    out.push(Violation {
                        path: path.to_owned(),
                        kind: ViolationKind::TokenBudgetExceeded {
                            bytes: meta.len(),
                            max_bytes: budget.max_bytes,
                            label: budget.label.to_string(),
                        },
                    });
                }
            }
        }
    }
}

/// Return true if the file contains a copyright line within the first 5 lines.
pub fn has_copyright(content: &str) -> bool {
    content
        .lines()
        .take(5)
        .any(|l| l.to_lowercase().contains("copyright"))
}

/// Match a markdown file path against the token-budget patterns.
/// Returns the first matching budget, or None for unlisted md files.
pub fn find_budget<'a>(root: &Path, path: &Path) -> Option<&'a Budget> {
    let rel = match path.strip_prefix(root) {
        Ok(r) => r,
        Err(_) => return None,
    };
    let rel_str = rel.to_string_lossy();
    let file_name = path.file_name()?.to_string_lossy().to_string();
    for budget in BUDGETS {
        if budget.pattern.ends_with('/') {
            if rel_str.contains(budget.pattern) {
                return Some(budget);
            }
        } else if file_name == budget.pattern {
            return Some(budget);
        }
    }
    None
}

/// Format a violation for human-readable output.
pub fn format_violation(v: &Violation) -> String {
    let p = v.path.display();
    match &v.kind {
        ViolationKind::TooManyLines { lines } => {
            format!("[LINES]        {p}  ({lines} lines, max 250)")
        }
        ViolationKind::TokenBudgetExceeded {
            bytes,
            max_bytes,
            label,
        } => format!("[TOKEN-BUDGET] {p}  ({bytes}B > {max_bytes}B, type: {label})"),
        ViolationKind::MissingCopyright => {
            format!("[COPYRIGHT]    {p}  (missing copyright header)")
        }
        ViolationKind::ConstitutionMissing { filename } => {
            format!("[CONSTITUTION] {filename}  (required file missing from project root)")
        }
    }
}

/// Entry point called from main.rs dispatch.
pub fn handle(path: PathBuf) -> Result<(), crate::cli_error::CliError> {
    let root = if path.as_os_str().is_empty() || path == std::path::Path::new(".") {
        std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
    } else {
        path
    };
    println!("Auditing: {}", root.display());
    let violations = audit(&root);
    if violations.is_empty() {
        println!("OK — no violations found.");
        return Ok(());
    }
    println!("\n{} violation(s) found:\n", violations.len());
    for v in &violations {
        println!("  {}", format_violation(v));
    }
    Err(crate::cli_error::CliError::ViolationsFound(format!(
        "{} violation(s) found",
        violations.len()
    )))
}

#[cfg(test)]
#[path = "cli_audit_tests.rs"]
mod tests;
