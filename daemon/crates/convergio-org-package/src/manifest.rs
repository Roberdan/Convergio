//! Org package manifest — parsed from manifest.toml inside a package.
//!
//! A package contains: manifest.toml, agents/*.toml, prompts/*.md,
//! migrations/*.sql. This module defines the manifest format and
//! validates it before installation.

use serde::{Deserialize, Serialize};

/// Top-level org package manifest, deserialized from manifest.toml.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgManifest {
    pub package: PackageMeta,
    #[serde(default)]
    pub permissions: PackagePermissions,
    #[serde(default)]
    pub budget: PackageBudget,
    #[serde(default)]
    pub delegation: DelegationConfig,
    #[serde(default)]
    pub templates: TemplatesConfig,
}

/// Custom project templates declared by the org package.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TemplatesConfig {
    /// Named templates mapping to relative paths inside the package.
    #[serde(default)]
    pub project: Vec<ProjectTemplate>,
}

/// A single project template available for `cvg project init --template`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectTemplate {
    /// Template name (used via --template flag).
    pub name: String,
    /// Language this template targets (rust/typescript/python).
    pub language: String,
    /// Relative path to the template directory inside the package.
    pub path: String,
    /// Human-readable description.
    #[serde(default)]
    pub description: Option<String>,
}

/// Package identity and metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackageMeta {
    /// Unique package name (e.g. "convergio-legal-team").
    pub name: String,
    /// SemVer version.
    pub version: String,
    /// Human-readable description.
    pub description: String,
    /// Author or organization.
    pub author: String,
    /// Minimum daemon version required.
    #[serde(default)]
    pub min_daemon_version: Option<String>,
    /// License identifier (SPDX).
    #[serde(default)]
    pub license: Option<String>,
}

/// Permissions the package requests at install time.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PackagePermissions {
    /// IPC channels the org can publish to.
    #[serde(default)]
    pub ipc_publish: Vec<String>,
    /// IPC channels the org can subscribe to.
    #[serde(default)]
    pub ipc_subscribe: Vec<String>,
    /// API route prefixes the org exposes.
    #[serde(default)]
    pub routes: Vec<String>,
    /// Whether the org can spawn subprocesses.
    #[serde(default)]
    pub allow_subprocess: bool,
    /// Network destinations the org can reach.
    #[serde(default)]
    pub network_allowlist: Vec<String>,
}

/// Budget constraints declared by the package.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PackageBudget {
    /// Max API calls per hour across all agents.
    pub max_api_calls_per_hour: u64,
    /// Max tokens per day across all agents.
    pub max_tokens_per_day: u64,
    /// Max compute seconds per day.
    pub max_compute_seconds: u64,
}

impl Default for PackageBudget {
    fn default() -> Self {
        Self {
            max_api_calls_per_hour: 500,
            max_tokens_per_day: 5_000_000,
            max_compute_seconds: 1800,
        }
    }
}

/// Delegation policy for inter-org communication.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DelegationConfig {
    /// Whether this org can delegate tasks to other orgs.
    #[serde(default)]
    pub can_delegate: bool,
    /// Whether this org can receive delegated tasks.
    #[serde(default)]
    pub can_receive: bool,
    /// Org names this org trusts for delegation.
    #[serde(default)]
    pub trusted_orgs: Vec<String>,
}

/// Validation errors for a manifest.
#[derive(Debug, thiserror::Error)]
pub enum ManifestError {
    #[error("parse error: {0}")]
    Parse(String),
    #[error("missing required field: {0}")]
    MissingField(String),
    #[error("invalid version: {0}")]
    InvalidVersion(String),
    #[error("name too long (max 64 chars): {0}")]
    NameTooLong(String),
    #[error("invalid name (alphanumeric + hyphens only): {0}")]
    InvalidName(String),
}

/// Parse and validate a manifest from TOML string.
pub fn parse_manifest(toml_str: &str) -> Result<OrgManifest, ManifestError> {
    let manifest: OrgManifest =
        toml::from_str(toml_str).map_err(|e| ManifestError::Parse(e.to_string()))?;
    validate(&manifest)?;
    Ok(manifest)
}

fn validate(m: &OrgManifest) -> Result<(), ManifestError> {
    if m.package.name.is_empty() {
        return Err(ManifestError::MissingField("package.name".into()));
    }
    if m.package.name.len() > 64 {
        return Err(ManifestError::NameTooLong(m.package.name.clone()));
    }
    if !m
        .package
        .name
        .chars()
        .all(|c| c.is_alphanumeric() || c == '-')
    {
        return Err(ManifestError::InvalidName(m.package.name.clone()));
    }
    if m.package.version.is_empty() {
        return Err(ManifestError::MissingField("package.version".into()));
    }
    validate_semver(&m.package.version)?;
    if m.package.description.is_empty() {
        return Err(ManifestError::MissingField("package.description".into()));
    }
    if m.package.author.is_empty() {
        return Err(ManifestError::MissingField("package.author".into()));
    }
    Ok(())
}

fn validate_semver(v: &str) -> Result<(), ManifestError> {
    let parts: Vec<&str> = v.split('.').collect();
    if parts.len() != 3 {
        return Err(ManifestError::InvalidVersion(v.to_string()));
    }
    for p in &parts {
        if p.parse::<u32>().is_err() {
            return Err(ManifestError::InvalidVersion(v.to_string()));
        }
    }
    Ok(())
}

#[cfg(test)]
#[path = "manifest_tests.rs"]
mod tests;
