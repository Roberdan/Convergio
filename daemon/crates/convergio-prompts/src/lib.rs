//! convergio-prompts — Prompt management, skill registry, A/B testing.
//!
//! Provides versioned prompt templates with variable substitution,
//! skill registry for agent capability discovery, token optimization,
//! A/B testing, and immutable prompt injection at agent spawn.

pub mod ab_test;
pub mod ext;
pub mod optimizer;
pub mod pipeline;
pub mod render;
pub mod routes;
pub mod schema;
pub mod seed;
pub mod seed_skills;
pub mod skills;
pub mod spawn;
pub mod store;
pub mod types;
