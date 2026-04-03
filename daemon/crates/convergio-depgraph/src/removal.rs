//! Module removal safety check — blocks removal if it breaks dependents.

use convergio_types::manifest::Manifest;
use std::collections::HashMap;

/// Result of checking whether a module can be safely removed.
#[derive(Debug, Clone, serde::Serialize)]
pub struct RemovalCheck {
    /// Module being considered for removal.
    pub module_id: String,
    /// Whether removal is safe (no required dependents broken).
    pub safe: bool,
    /// Modules that would break if this module is removed.
    pub would_break: Vec<BrokenDependent>,
}

/// A module that depends on a capability that would be lost.
#[derive(Debug, Clone, serde::Serialize)]
pub struct BrokenDependent {
    pub module_id: String,
    pub capability: String,
    pub required: bool,
}

/// Check if removing `target_id` would break any other module's
/// required dependencies.
pub fn check_removal(target_id: &str, manifests: &[Manifest]) -> RemovalCheck {
    // Find capabilities provided by target module.
    let target = manifests.iter().find(|m| m.id == target_id);
    let provided_caps: Vec<String> = match target {
        Some(m) => m.provides.iter().map(|c| c.name.clone()).collect(),
        None => {
            return RemovalCheck {
                module_id: target_id.to_string(),
                safe: true,
                would_break: vec![],
            };
        }
    };

    // Check which other providers exist for each capability.
    let mut cap_providers: HashMap<String, Vec<String>> = HashMap::new();
    for m in manifests {
        for cap in &m.provides {
            cap_providers
                .entry(cap.name.clone())
                .or_default()
                .push(m.id.clone());
        }
    }

    // Find dependents that would break.
    let mut would_break = Vec::new();
    for m in manifests {
        if m.id == target_id {
            continue;
        }
        for dep in &m.requires {
            if provided_caps.contains(&dep.capability) {
                // Check if another module also provides this.
                let providers = cap_providers
                    .get(&dep.capability)
                    .cloned()
                    .unwrap_or_default();
                let alt_exists = providers.iter().any(|p| p != target_id);
                if !alt_exists {
                    would_break.push(BrokenDependent {
                        module_id: m.id.clone(),
                        capability: dep.capability.clone(),
                        required: dep.required,
                    });
                }
            }
        }
    }

    let safe = !would_break.iter().any(|b| b.required);

    RemovalCheck {
        module_id: target_id.to_string(),
        safe,
        would_break,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use convergio_types::manifest::{Capability, Dependency, ModuleKind};

    fn cap(name: &str) -> Capability {
        Capability {
            name: name.into(),
            version: "0.1.0".into(),
            description: String::new(),
        }
    }

    fn dep(name: &str, required: bool) -> Dependency {
        Dependency {
            capability: name.into(),
            version_req: ">=0.1.0".into(),
            required,
        }
    }

    fn manifest(id: &str, provides: Vec<Capability>, requires: Vec<Dependency>) -> Manifest {
        Manifest {
            id: id.into(),
            description: String::new(),
            version: "0.1.0".into(),
            kind: ModuleKind::Core,
            provides,
            requires,
            agent_tools: vec![],
        }
    }

    #[test]
    fn removal_safe_when_no_dependents() {
        let manifests = vec![
            manifest("types", vec![cap("core")], vec![]),
            manifest("unused", vec![cap("nothing")], vec![]),
        ];
        let result = check_removal("unused", &manifests);
        assert!(result.safe);
        assert!(result.would_break.is_empty());
    }

    #[test]
    fn removal_blocked_with_required_dependent() {
        let manifests = vec![
            manifest("types", vec![cap("core")], vec![]),
            manifest("db", vec![], vec![dep("core", true)]),
        ];
        let result = check_removal("types", &manifests);
        assert!(!result.safe);
        assert_eq!(result.would_break.len(), 1);
        assert_eq!(result.would_break[0].module_id, "db");
    }

    #[test]
    fn removal_ok_with_optional_dependent() {
        let manifests = vec![
            manifest("types", vec![cap("core")], vec![]),
            manifest("ext", vec![], vec![dep("core", false)]),
        ];
        let result = check_removal("types", &manifests);
        assert!(result.safe);
        assert_eq!(result.would_break.len(), 1);
    }

    #[test]
    fn removal_of_nonexistent_module() {
        let manifests = vec![manifest("types", vec![cap("core")], vec![])];
        let result = check_removal("ghost", &manifests);
        assert!(result.safe);
    }

    #[test]
    fn removal_ok_when_alt_provider_exists() {
        let manifests = vec![
            manifest("provider-a", vec![cap("shared")], vec![]),
            manifest("provider-b", vec![cap("shared")], vec![]),
            manifest("consumer", vec![], vec![dep("shared", true)]),
        ];
        let result = check_removal("provider-a", &manifests);
        assert!(result.safe);
    }
}
