//! Tests for dependency graph validation.

use super::*;
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

fn cap(name: &str, ver: &str) -> Capability {
    Capability {
        name: name.into(),
        version: ver.into(),
        description: format!("{name} capability"),
    }
}

fn dep(cap_name: &str, ver_req: &str, required: bool) -> Dependency {
    Dependency {
        capability: cap_name.into(),
        version_req: ver_req.into(),
        required,
    }
}

fn manifest(id: &str, provides: Vec<Capability>, requires: Vec<Dependency>) -> Manifest {
    Manifest {
        id: id.into(),
        description: format!("{id} module"),
        version: "0.1.0".into(),
        kind: ModuleKind::Core,
        provides,
        requires,
        agent_tools: vec![],
    }
}

#[test]
fn valid_graph_passes() {
    let manifests = vec![
        manifest("types", vec![cap("types-core", "0.1.0")], vec![]),
        manifest(
            "db",
            vec![cap("db-pool", "0.1.0")],
            vec![dep("types-core", ">=0.1.0", true)],
        ),
    ];
    assert!(DepGraph::validate(&manifests).is_ok());
}

#[test]
fn missing_required_dep_fails() {
    let manifests = vec![manifest(
        "mesh",
        vec![],
        vec![dep("nonexistent", ">=1.0.0", true)],
    )];
    let errors = DepGraph::validate(&manifests).unwrap_err();
    assert!(errors.iter().any(|e| matches!(
        e,
        GraphError::MissingDependency { capability, .. }
        if capability == "nonexistent"
    )));
}

#[test]
fn missing_optional_dep_ok() {
    let manifests = vec![manifest(
        "mesh",
        vec![],
        vec![dep("optional-cap", ">=1.0.0", false)],
    )];
    assert!(DepGraph::validate(&manifests).is_ok());
}

#[test]
fn circular_dep_detected() {
    let manifests = vec![
        manifest(
            "alpha",
            vec![cap("cap-a", "1.0.0")],
            vec![dep("cap-b", ">=1.0.0", true)],
        ),
        manifest(
            "beta",
            vec![cap("cap-b", "1.0.0")],
            vec![dep("cap-a", ">=1.0.0", true)],
        ),
    ];
    let errors = DepGraph::validate(&manifests).unwrap_err();
    assert!(errors
        .iter()
        .any(|e| matches!(e, GraphError::CircularDependency { .. })));
}

#[test]
fn semver_mismatch_detected() {
    let manifests = vec![
        manifest("types", vec![cap("core", "0.1.0")], vec![]),
        manifest("consumer", vec![], vec![dep("core", ">=2.0.0", true)]),
    ];
    let errors = DepGraph::validate(&manifests).unwrap_err();
    assert!(errors.iter().any(|e| matches!(
        e,
        GraphError::SemVerMismatch { capability, .. }
        if capability == "core"
    )));
}

#[test]
fn graph_serializes_to_json() {
    let manifests = vec![
        manifest("types", vec![cap("core", "0.1.0")], vec![]),
        manifest(
            "db",
            vec![cap("pool", "0.1.0")],
            vec![dep("core", ">=0.1.0", true)],
        ),
    ];
    let graph = DepGraph::from_manifests(&manifests);
    let json = serde_json::to_string(&graph).unwrap();
    assert!(json.contains("\"nodes\""));
    assert!(json.contains("\"edges\""));
    assert!(json.contains("types"));
    assert!(json.contains("db"));
}

#[test]
fn no_self_cycle_false_positive() {
    // A module providing cap-a and requiring cap-a should not self-cycle
    // because we skip self-edges in detect_cycle.
    let manifests = vec![manifest(
        "self-ref",
        vec![cap("cap-x", "1.0.0")],
        vec![dep("cap-x", ">=1.0.0", true)],
    )];
    assert!(DepGraph::validate(&manifests).is_ok());
}

#[test]
fn three_node_cycle() {
    let manifests = vec![
        manifest(
            "a",
            vec![cap("cap-a", "1.0.0")],
            vec![dep("cap-c", ">=1.0.0", true)],
        ),
        manifest(
            "b",
            vec![cap("cap-b", "1.0.0")],
            vec![dep("cap-a", ">=1.0.0", true)],
        ),
        manifest(
            "c",
            vec![cap("cap-c", "1.0.0")],
            vec![dep("cap-b", ">=1.0.0", true)],
        ),
    ];
    let errors = DepGraph::validate(&manifests).unwrap_err();
    assert!(errors
        .iter()
        .any(|e| matches!(e, GraphError::CircularDependency { .. })));
}

#[test]
fn default_depgraph_is_empty() {
    let g = DepGraph::default();
    assert!(g.nodes.is_empty());
    assert!(g.edges.is_empty());
}
