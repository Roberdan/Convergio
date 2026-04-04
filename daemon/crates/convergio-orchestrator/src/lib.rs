//! convergio-orchestrator — Plans, tasks, waves, Thor gate, reaper.
//!
//! Implements Extension: owns plans, tasks, waves, deliverables, projects.

pub mod actions;
pub mod aggregation_routes;
pub mod approval;
pub mod approval_routes;
pub mod artifact_bundle;
pub mod artifact_routes;
pub mod artifacts;
pub mod bundle_routes;
pub mod compensation;
pub mod compensation_routes;
pub mod evaluation;
pub mod evaluation_routes;
pub mod executor;
pub mod ext;
pub mod gates;
pub mod handlers;
pub mod plan_hierarchy;
pub mod plan_review;
pub mod plan_routes;
pub mod plan_routes_ext;
pub mod plan_validate;
pub mod pm_routes;
pub mod policy;
pub mod reactor;
pub mod reaper;
pub mod rollback;
pub mod scaffold;
pub mod scaffold_gen;
pub mod scaffold_templates;
pub mod schema;
pub mod schema_compensation;
pub mod schema_evaluation;
pub mod schema_tracking;
pub mod task_routes;
pub mod tracking_routes;
pub mod types;
pub mod validator;

pub use ext::OrchestratorExtension;
