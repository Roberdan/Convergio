//! Seed data: core_utility agents (19 agents).

use crate::types::{AgentCategory, AgentInput};

fn a(name: &str, role: &str, tier: &str, esc: Option<&str>) -> AgentInput {
    AgentInput {
        name: name.into(),
        role: role.into(),
        org: "convergio".into(),
        category: AgentCategory::CoreUtility,
        model_tier: tier.into(),
        max_tokens: 200_000,
        hourly_budget: 0.0,
        capabilities: vec![],
        prompt_ref: None,
        escalation_target: esc.map(Into::into),
    }
}

pub fn agents() -> Vec<AgentInput> {
    vec![
        a("ali-orchestrator", "Chief of Staff — orchestrates all agent work", "t4", None),
        a("thor", "Validation guardian — reviews all submitted work", "t4", Some("ali-orchestrator")),
        a("wanda", "Workspace manager — worktree lifecycle", "t2", Some("ali-orchestrator")),
        a("sentinel", "Security sentinel — monitors for threats", "t3", Some("ali-orchestrator")),
        a("taskmaster", "Task queue manager — assigns and tracks tasks", "t2", Some("ali-orchestrator")),
        a("socrates", "Socratic reviewer — asks probing questions", "t3", Some("thor")),
        a("diana", "Dependency analyst — tracks inter-module deps", "t2", Some("ali-orchestrator")),
        a("marcus", "Metrics collector — gathers system telemetry", "t1", Some("ali-orchestrator")),
        a("xavier", "Context optimizer — compacts prompts and context", "t3", Some("ali-orchestrator")),
        a("po", "Product owner — prioritizes backlog items", "t3", Some("ali-orchestrator")),
        a("plan-reviewer", "Plan review — validates plan structure", "t3", Some("thor")),
        a("plan-business-advisor", "Business advisor for plan feasibility", "t3", Some("ali-orchestrator")),
        a("plan-post-mortem", "Post-mortem analyst — learns from failures", "t3", Some("ali-orchestrator")),
        a("compliance-validator", "Validates compliance rules in code", "t2", Some("elena")),
        a("context-optimizer", "Optimizes context window usage", "t2", Some("xavier")),
        a("deep-repo-auditor", "Deep audit of repository structure", "t3", Some("ali-orchestrator")),
        a("design-validator", "Validates UI against design system", "t2", Some("jony")),
        a("doc-validator", "Validates documentation completeness", "t2", Some("ali-orchestrator")),
        a("strategic-planner", "Long-term strategic planning", "t4", Some("ali-orchestrator")),
    ]
}
