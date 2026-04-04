// Evidence types — shared across the crate.

use serde::{Deserialize, Serialize};

/// Known evidence types that can be recorded for a task.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceKind {
    TestPass,
    BuildPass,
    LintPass,
    CommitHash,
    Artifact,
    CurlOutput,
    ReviewPass,
    Document,
}

impl EvidenceKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::TestPass => "test_pass",
            Self::BuildPass => "build_pass",
            Self::LintPass => "lint_pass",
            Self::CommitHash => "commit_hash",
            Self::Artifact => "artifact",
            Self::CurlOutput => "curl_output",
            Self::ReviewPass => "review_pass",
            Self::Document => "document",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "test_pass" => Some(Self::TestPass),
            "build_pass" => Some(Self::BuildPass),
            "lint_pass" => Some(Self::LintPass),
            "commit_hash" => Some(Self::CommitHash),
            "artifact" => Some(Self::Artifact),
            "curl_output" => Some(Self::CurlOutput),
            "review_pass" => Some(Self::ReviewPass),
            "document" => Some(Self::Document),
            _ => None,
        }
    }
}

/// A recorded evidence entry for a task.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvidenceRecord {
    pub id: i64,
    pub task_id: i64,
    pub evidence_type: String,
    pub command: String,
    pub output_summary: String,
    pub exit_code: i64,
    pub created_at: String,
}

/// Result of a pre-flight check before spawning an agent.
#[derive(Debug, Clone, Serialize)]
pub struct PreflightResult {
    pub passed: bool,
    pub checks: Vec<PreflightCheck>,
}

#[derive(Debug, Clone, Serialize)]
pub struct PreflightCheck {
    pub name: String,
    pub passed: bool,
    pub detail: String,
}

impl PreflightResult {
    pub fn failed_checks(&self) -> Vec<&PreflightCheck> {
        self.checks.iter().filter(|c| !c.passed).collect()
    }
}

/// A checklist item that must be satisfied before a task can be marked done.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChecklistItem {
    pub name: String,
    pub required: bool,
    pub evidence_type: String,
}

/// Default closure checklist: the minimum evidence required for done.
pub fn default_closure_checklist() -> Vec<ChecklistItem> {
    vec![
        ChecklistItem {
            name: "tests_passed".into(),
            required: true,
            evidence_type: "test_pass".into(),
        },
        ChecklistItem {
            name: "build_passed".into(),
            required: true,
            evidence_type: "build_pass".into(),
        },
        ChecklistItem {
            name: "commit_recorded".into(),
            required: true,
            evidence_type: "commit_hash".into(),
        },
    ]
}

/// Gate violation — returned when a gate blocks a transition.
#[derive(Debug, Clone, Serialize)]
pub struct GateViolation {
    pub gate: String,
    pub task_id: i64,
    pub detail: String,
}

/// Commit-to-task match record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommitTaskMatch {
    pub id: i64,
    pub task_id: i64,
    pub commit_hash: String,
    pub commit_message: String,
    pub matched_at: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn evidence_kind_roundtrip() {
        for kind in [
            EvidenceKind::TestPass,
            EvidenceKind::BuildPass,
            EvidenceKind::LintPass,
            EvidenceKind::CommitHash,
            EvidenceKind::Artifact,
            EvidenceKind::CurlOutput,
            EvidenceKind::ReviewPass,
            EvidenceKind::Document,
        ] {
            let s = kind.as_str();
            assert_eq!(EvidenceKind::parse(s), Some(kind));
        }
    }

    #[test]
    fn evidence_kind_unknown() {
        assert_eq!(EvidenceKind::parse("unknown"), None);
    }

    #[test]
    fn default_checklist_has_required_items() {
        let cl = default_closure_checklist();
        assert_eq!(cl.len(), 3);
        assert!(cl.iter().all(|i| i.required));
    }

    #[test]
    fn preflight_result_failed_checks() {
        let r = PreflightResult {
            passed: false,
            checks: vec![
                PreflightCheck {
                    name: "a".into(),
                    passed: true,
                    detail: "ok".into(),
                },
                PreflightCheck {
                    name: "b".into(),
                    passed: false,
                    detail: "fail".into(),
                },
            ],
        };
        assert_eq!(r.failed_checks().len(), 1);
        assert_eq!(r.failed_checks()[0].name, "b");
    }
}
