//! convergio-org — Org chart, inter-org comms, provisioner.
//!
//! Extension: owns notifications, notification_queue, notification_deliveries,
//! decision_log. Provides org design from mission/repo, provisioning, orgchart rendering.

pub mod ext;
pub mod factory;
pub mod orgchart;
pub mod provisioner;
pub mod repo_scanner;
mod repo_scanner_helpers;
pub mod routes;
pub mod routes_decisions;
pub mod routes_members;
pub mod routes_notify;

pub use ext::OrgExtension;
pub use factory::{
    design_org_from_mission, design_org_from_repo, slugify, AgentSpec, Department, NightAgentSpec,
    OrgBlueprint,
};
pub use orgchart::{render_orgchart, render_orgchart_compact};
pub use provisioner::{provision_org, ProvisionResult};
pub use repo_scanner::{scan_repo, CiInfo, RepoProfile, RepoStructure};

#[cfg(test)]
mod tests;
