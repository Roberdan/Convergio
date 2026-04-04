//! convergio-evidence — Evidence gate, checklist enforcement, workflow automation.
//!
//! Implements Extension: owns task_evidence, evidence_checklist tables.
//! Provides gates that block status transitions without verifiable evidence,
//! pre-flight validation before agent spawn, and Thor auto-trigger on wave completion.

pub mod evidence;
pub mod ext;
pub mod gates;
pub mod preflight;
pub mod routes;
pub mod schema;
pub mod types;
pub mod workflow;

pub use ext::EvidenceExtension;
