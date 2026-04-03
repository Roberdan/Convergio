// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// `cvg plan template` — generate an example spec YAML with all supported fields.

/// Return the canonical example spec YAML.
/// Kept as a standalone function so tests can assert on structure.
pub fn example_spec_yaml() -> &'static str {
    r#"# Convergio Plan Spec — YAML Template
# Import: cvg plan import <plan_id> this-file.yaml

waves:
  - id: "W1"
    name: "Foundation"          # also accepts: title
    depends_on: null            # wave dependency (e.g. "W1")
    estimated_hours: 8          # default: 8
    tasks:
      - id: "T1-01"
        title: "Implement feature X"   # also accepts: do, summary
        type: feature                  # feature|bugfix|test|planning|analysis|review|docs
        priority: P1                   # P0|P1|P2 (default: P1)
        description: "Detailed description of what to build"
        model: gpt-5.3-codex          # auto-inferred from type if absent
        assignee: null                 # optional: copilot|claude
        output_type: pr                # pr|document|analysis|design|legal_opinion
        validator_agent: thor          # auto-inferred from output_type if absent
        effort_level: 2                # 1-3, auto-inferred from file count if absent
        files:                         # files this task modifies
          - src/module/feature.rs
          - src/module/feature_tests.rs
        verify:                        # verify commands (auto-generated from files if empty)
          - "test -f src/module/feature.rs"
          - "cargo test --lib feature"
        test_criteria: "cargo test --lib feature passes"

  - id: "W2"
    name: "Integration"
    depends_on: "W1"
    estimated_hours: 4
    tasks:
      - id: "T2-01"
        do: "Write integration tests"  # 'do' is an alias for 'title'
        type: test
        files:
          - tests/integration.rs
"#
}

/// Print the template to stdout.
pub fn print_template() {
    print!("{}", example_spec_yaml());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn template_contains_required_structure() {
        let yaml = example_spec_yaml();
        assert!(yaml.contains("waves:"), "must have waves key");
        assert!(yaml.contains("tasks:"), "must have tasks key");
        assert!(yaml.contains("id:"), "must have id field");
        assert!(yaml.contains("title:"), "must have title field");
        assert!(yaml.contains("files:"), "must have files field");
        assert!(yaml.contains("verify:"), "must have verify field");
    }

    #[test]
    fn template_documents_aliases() {
        let yaml = example_spec_yaml();
        assert!(yaml.contains("do:"), "must document 'do' alias");
        assert!(yaml.contains("also accepts: title"), "must note title alias for name");
        assert!(yaml.contains("also accepts: do, summary"), "must note do/summary aliases");
    }

    #[test]
    fn template_is_valid_yaml() {
        let yaml = example_spec_yaml();
        let parsed: serde_yaml::Value = serde_yaml::from_str(yaml)
            .expect("template must be valid YAML");
        let waves = parsed.get("waves").expect("must have waves key");
        assert!(waves.is_sequence(), "waves must be an array");
    }

    #[test]
    fn template_documents_all_task_fields() {
        let yaml = example_spec_yaml();
        let expected_fields = [
            "id:", "title:", "type:", "priority:", "description:",
            "model:", "assignee:", "output_type:", "validator_agent:",
            "effort_level:", "files:", "verify:", "test_criteria:",
        ];
        for field in expected_fields {
            assert!(yaml.contains(field), "template must document field '{field}'");
        }
    }
}
