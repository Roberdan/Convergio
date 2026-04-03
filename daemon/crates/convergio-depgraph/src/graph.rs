//! Core dependency graph: build from manifests, detect cycles, validate deps.

use std::collections::{HashMap, HashSet, VecDeque};

use convergio_types::manifest::{Capability, Dependency, Manifest};
use serde::{Deserialize, Serialize};

/// Validation error kinds produced during graph analysis.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum GraphError {
    /// A required dependency is not provided by any loaded module.
    MissingDependency {
        module: String,
        capability: String,
        version_req: String,
    },
    /// Two or more modules form a dependency cycle.
    CircularDependency { cycle: Vec<String> },
    /// A capability version does not satisfy a consumer's version_req.
    SemVerMismatch {
        module: String,
        capability: String,
        required: String,
        provided: String,
    },
}

/// A node in the serializable dependency graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphNode {
    pub id: String,
    pub version: String,
    pub kind: String,
    pub provides: Vec<Capability>,
    pub requires: Vec<Dependency>,
}

/// An edge in the serializable dependency graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GraphEdge {
    pub from: String,
    pub to: String,
    pub capability: String,
}

/// The full dependency graph — serializable to JSON for UI consumption.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DepGraph {
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
}

impl Default for DepGraph {
    fn default() -> Self {
        Self::new()
    }
}

impl DepGraph {
    pub fn new() -> Self {
        Self {
            nodes: Vec::new(),
            edges: Vec::new(),
        }
    }

    /// Build graph from a set of manifests.
    pub fn from_manifests(manifests: &[Manifest]) -> Self {
        let cap_providers = build_capability_map(manifests);
        let mut nodes = Vec::new();
        let mut edges = Vec::new();

        for m in manifests {
            nodes.push(GraphNode {
                id: m.id.clone(),
                version: m.version.clone(),
                kind: format!("{:?}", m.kind),
                provides: m.provides.clone(),
                requires: m.requires.clone(),
            });
            for dep in &m.requires {
                if let Some(provider) = cap_providers.get(&dep.capability) {
                    edges.push(GraphEdge {
                        from: m.id.clone(),
                        to: provider.clone(),
                        capability: dep.capability.clone(),
                    });
                }
            }
        }

        Self { nodes, edges }
    }

    /// Validate the graph: check missing deps, semver, cycles.
    /// Returns Ok(()) if valid, Err with all errors found.
    pub fn validate(manifests: &[Manifest]) -> Result<(), Vec<GraphError>> {
        let mut errors = Vec::new();

        let cap_map = build_capability_map(manifests);
        let cap_versions = build_capability_version_map(manifests);

        // Check missing + semver
        for m in manifests {
            for dep in &m.requires {
                match cap_map.get(&dep.capability) {
                    None if dep.required => {
                        errors.push(GraphError::MissingDependency {
                            module: m.id.clone(),
                            capability: dep.capability.clone(),
                            version_req: dep.version_req.clone(),
                        });
                    }
                    Some(_provider) => {
                        if let Some(provided_ver) = cap_versions.get(&dep.capability) {
                            if let Err(e) =
                                crate::semver_check::check(provided_ver, &dep.version_req)
                            {
                                errors.push(GraphError::SemVerMismatch {
                                    module: m.id.clone(),
                                    capability: dep.capability.clone(),
                                    required: dep.version_req.clone(),
                                    provided: e.provided,
                                });
                            }
                        }
                    }
                    _ => {} // optional dep missing — ok
                }
            }
        }

        // Cycle detection
        if let Some(cycle) = detect_cycle(manifests, &cap_map) {
            errors.push(GraphError::CircularDependency { cycle });
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}

/// Map capability name -> provider module id.
fn build_capability_map(manifests: &[Manifest]) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for m in manifests {
        for cap in &m.provides {
            map.insert(cap.name.clone(), m.id.clone());
        }
    }
    map
}

/// Map capability name -> provided version string.
fn build_capability_version_map(manifests: &[Manifest]) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for m in manifests {
        for cap in &m.provides {
            map.insert(cap.name.clone(), cap.version.clone());
        }
    }
    map
}

/// Detect cycles using BFS-based topological sort (Kahn's algorithm).
/// Returns the first cycle found, or None.
fn detect_cycle(manifests: &[Manifest], cap_map: &HashMap<String, String>) -> Option<Vec<String>> {
    let ids: Vec<&str> = manifests.iter().map(|m| m.id.as_str()).collect();
    let id_set: HashSet<&str> = ids.iter().copied().collect();

    // Build adjacency: module -> set of modules it depends on
    let mut deps: HashMap<&str, HashSet<&str>> = HashMap::new();
    let mut rdeps: HashMap<&str, HashSet<&str>> = HashMap::new();
    for id in &ids {
        deps.insert(id, HashSet::new());
        rdeps.insert(id, HashSet::new());
    }

    for m in manifests {
        for dep in &m.requires {
            if let Some(provider) = cap_map.get(&dep.capability) {
                if id_set.contains(provider.as_str()) && provider.as_str() != m.id.as_str() {
                    deps.get_mut(m.id.as_str())
                        .unwrap()
                        .insert(provider.as_str());
                    rdeps
                        .get_mut(provider.as_str())
                        .unwrap()
                        .insert(m.id.as_str());
                }
            }
        }
    }

    // Kahn's: start with nodes that have zero in-degree
    let mut in_degree: HashMap<&str, usize> = HashMap::new();
    for id in &ids {
        in_degree.insert(id, deps[id].len());
    }

    let mut queue: VecDeque<&str> = VecDeque::new();
    for (&id, &deg) in &in_degree {
        if deg == 0 {
            queue.push_back(id);
        }
    }

    let mut sorted_count = 0usize;
    while let Some(node) = queue.pop_front() {
        sorted_count += 1;
        if let Some(dependents) = rdeps.get(node) {
            for &dep in dependents {
                let d = in_degree.get_mut(dep).unwrap();
                *d -= 1;
                if *d == 0 {
                    queue.push_back(dep);
                }
            }
        }
    }

    if sorted_count == ids.len() {
        return None; // no cycle
    }

    // Extract cycle participants
    let cycle: Vec<String> = in_degree
        .iter()
        .filter(|(_, &deg)| deg > 0)
        .map(|(&id, _)| id.to_string())
        .collect();

    Some(cycle)
}

#[cfg(test)]
#[path = "graph_tests.rs"]
mod tests;
