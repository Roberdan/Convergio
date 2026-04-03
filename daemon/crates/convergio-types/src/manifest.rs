//! Semantic manifest — every extension declares what it is, provides, and requires.

/// What kind of module this is.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum ModuleKind {
    /// Core infrastructure — must always be present.
    Core,
    /// Platform service — orchestration layer.
    Platform,
    /// Pluggable extension — optional, can be added/removed.
    Extension,
    /// External integration — registered via HTTP bridge.
    Integration,
}

/// The manifest — identity + capabilities + dependencies.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Manifest {
    /// Unique identifier (e.g. "convergio-mesh").
    pub id: String,
    /// Human and LLM readable description.
    pub description: String,
    /// SemVer version.
    pub version: String,
    /// Classification.
    pub kind: ModuleKind,
    /// What this module provides to the system.
    pub provides: Vec<Capability>,
    /// What this module requires from the system.
    pub requires: Vec<Dependency>,
    /// Tools that agents can invoke through this module.
    pub agent_tools: Vec<ToolSpec>,
}

/// A capability provided by a module.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Capability {
    /// Capability name (e.g. "peer-sync").
    pub name: String,
    /// SemVer version of this capability.
    pub version: String,
    /// What it does — for routing and LLM reasoning.
    pub description: String,
}

/// A dependency required by a module.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Dependency {
    /// Required capability name.
    pub capability: String,
    /// SemVer version requirement (e.g. ">=2.0, <3.0").
    pub version_req: String,
    /// If false, the module degrades gracefully when this is absent.
    pub required: bool,
}

/// A tool that agents can invoke.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ToolSpec {
    pub name: String,
    pub description: String,
    pub parameters_schema: serde_json::Value,
}
