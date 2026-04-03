//! Seed data: technical_development agents (10 agents).

use crate::types::{AgentCategory, AgentInput};

fn a(name: &str, role: &str, tier: &str, esc: Option<&str>) -> AgentInput {
    AgentInput {
        name: name.into(),
        role: role.into(),
        org: "convergio".into(),
        category: AgentCategory::TechnicalDevelopment,
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
        a(
            "baccio",
            "Executor — implements code changes from plans",
            "t3",
            Some("thor"),
        ),
        a(
            "rex",
            "Refactoring expert — improves code quality",
            "t3",
            Some("thor"),
        ),
        a(
            "task-executor",
            "General task executor for plan steps",
            "t3",
            Some("thor"),
        ),
        a(
            "task-executor-tdd",
            "TDD executor — red-green-refactor",
            "t3",
            Some("thor"),
        ),
        a(
            "dario-debugger",
            "Debugger — investigates and fixes bugs",
            "t3",
            Some("baccio"),
        ),
        a(
            "marco-devops",
            "DevOps engineer — CI/CD and infra",
            "t2",
            Some("ali-orchestrator"),
        ),
        a(
            "omri-data-scientist",
            "Data scientist — analytics and ML",
            "t3",
            Some("ali-orchestrator"),
        ),
        a(
            "otto-performance",
            "Performance engineer — profiling and opt",
            "t3",
            Some("baccio"),
        ),
        a(
            "paolo-best-practices",
            "Best practices enforcer",
            "t2",
            Some("thor"),
        ),
        a(
            "adversarial-debugger",
            "Adversarial testing — finds edge cases",
            "t3",
            Some("thor"),
        ),
    ]
}
