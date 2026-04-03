//! Core types for prompt management and skill registry.

use serde::{Deserialize, Serialize};

/// A versioned prompt template with variable placeholders.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptTemplate {
    pub id: String,
    pub name: String,
    pub version: u32,
    /// Template body with `{{variable}}` placeholders.
    pub body: String,
    /// Variable declarations: name -> description.
    pub variables: Vec<PromptVariable>,
    /// Optional category (e.g. "agent-role", "system", "task").
    pub category: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    /// Whether this is the active version for its name.
    pub active: bool,
}

/// A variable declared in a prompt template.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptVariable {
    pub name: String,
    pub description: String,
    pub required: bool,
    pub default_value: Option<String>,
}

/// Request to create or update a prompt template.
#[derive(Debug, Clone, Deserialize)]
pub struct PromptInput {
    pub name: String,
    pub body: String,
    pub variables: Vec<PromptVariable>,
    pub category: Option<String>,
}

/// A skill registered by an agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Skill {
    pub id: String,
    pub agent: String,
    pub host: String,
    pub capability: String,
    pub confidence: f64,
    pub description: String,
    pub last_used: Option<String>,
    pub registered_at: String,
}

/// Request to register a skill.
#[derive(Debug, Clone, Deserialize)]
pub struct SkillInput {
    pub agent: String,
    pub host: String,
    pub capability: String,
    pub confidence: f64,
    pub description: String,
}

/// Result of an A/B test comparison.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AbTestResult {
    pub test_id: String,
    pub prompt_a_id: String,
    pub prompt_b_id: String,
    pub task_ref: String,
    pub winner: Option<String>,
    pub tokens_a: u64,
    pub tokens_b: u64,
    pub score_a: f64,
    pub score_b: f64,
    pub created_at: String,
}

/// Token usage stats for a prompt.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenStats {
    pub prompt_id: String,
    pub total_tokens: u64,
    pub usage_count: u64,
    pub avg_tokens: f64,
}

/// An immutable snapshot of a prompt bound to an agent execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpawnedPrompt {
    pub spawn_id: String,
    pub agent: String,
    pub task_id: String,
    /// The fully rendered prompt, frozen at spawn time.
    pub rendered_body: String,
    pub prompt_template_id: String,
    pub prompt_version: u32,
    pub spawned_at: String,
}

/// Prompt search query parameters.
#[derive(Debug, Clone, Deserialize, Default)]
pub struct PromptQuery {
    pub name: Option<String>,
    pub category: Option<String>,
    pub active_only: Option<bool>,
}

/// Skill search query parameters.
#[derive(Debug, Clone, Deserialize, Default)]
pub struct SkillQuery {
    pub capability: Option<String>,
    pub agent: Option<String>,
    pub min_confidence: Option<f64>,
}

/// A declarative pipeline — ordered steps referencing prompt templates.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub steps: Vec<PipelineStep>,
    pub active: bool,
    pub created_at: String,
    pub updated_at: String,
}

/// A single step in a pipeline.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineStep {
    pub order: u32,
    pub skill: String,
    pub prompt_name: String,
    pub agent: Option<String>,
    pub condition: Option<String>,
}

/// Request to create a pipeline.
#[derive(Debug, Clone, Deserialize)]
pub struct PipelineInput {
    pub name: String,
    pub description: String,
    pub steps: Vec<PipelineStep>,
}
