//! convergio-orchestrator — Plans, tasks, waves, Thor gate, reaper.
//!
//! Implements Extension: owns plans, tasks, waves, deliverables, projects.

pub mod actions;
pub mod approval;
pub mod executor;
pub mod ext;
pub mod handlers;
pub mod plan_hierarchy;
pub mod plan_routes;
pub mod plan_routes_ext;
pub mod policy;
pub mod reactor;
pub mod reaper;
pub mod rollback;
pub mod scaffold;
pub mod scaffold_gen;
pub mod scaffold_templates;
pub mod schema;
pub mod task_routes;
pub mod types;
pub mod validator;

pub use ext::OrchestratorExtension;
