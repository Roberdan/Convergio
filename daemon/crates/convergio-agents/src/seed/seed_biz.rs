//! Seed data: business_operations + leadership_strategy agents (17 agents).

use crate::types::{AgentCategory, AgentInput};

fn biz(name: &str, role: &str, tier: &str, esc: Option<&str>) -> AgentInput {
    AgentInput {
        name: name.into(),
        role: role.into(),
        org: "convergio".into(),
        category: AgentCategory::BusinessOperations,
        model_tier: tier.into(),
        max_tokens: 200_000,
        hourly_budget: 0.0,
        capabilities: vec![],
        prompt_ref: None,
        escalation_target: esc.map(Into::into),
    }
}

fn lead(name: &str, role: &str, tier: &str, esc: Option<&str>) -> AgentInput {
    AgentInput {
        name: name.into(),
        role: role.into(),
        org: "convergio".into(),
        category: AgentCategory::LeadershipStrategy,
        model_tier: tier.into(),
        max_tokens: 200_000,
        hourly_budget: 0.0,
        capabilities: vec![],
        prompt_ref: None,
        escalation_target: esc.map(Into::into),
    }
}

pub fn agents() -> Vec<AgentInput> {
    let mut v = vec![
        // business_operations (10)
        biz("andrea", "Sales and partnerships manager", "t2", Some("ali-orchestrator")),
        biz("sofia", "Customer success manager", "t2", Some("ali-orchestrator")),
        biz("marcello", "Marketing strategist", "t2", Some("ali-orchestrator")),
        biz("davide", "Product analytics lead", "t2", Some("ali-orchestrator")),
        biz("enrico", "Business development", "t2", Some("ali-orchestrator")),
        biz("fabio", "Operations manager", "t2", Some("ali-orchestrator")),
        biz("luke", "Growth hacker", "t2", Some("ali-orchestrator")),
        biz("anna", "HR and people ops", "t2", Some("ali-orchestrator")),
        biz("dave", "Technical writer", "t2", Some("ali-orchestrator")),
        biz("steve", "Community manager", "t2", Some("ali-orchestrator")),
    ];
    // leadership_strategy (7)
    v.extend([
        lead("ali-cos", "Chief of Staff — strategic oversight", "t4", None),
        lead("amy-cfo", "CFO — financial strategy and budgets", "t4", Some("ali-cos")),
        lead("antonio", "CTO — technical vision and architecture", "t4", Some("ali-cos")),
        lead("dan", "VP Engineering — delivery and velocity", "t4", Some("antonio")),
        lead("domik", "VP Product — roadmap and features", "t3", Some("ali-cos")),
        lead("matteo", "VP Design — design vision and brand", "t3", Some("ali-cos")),
        lead("satya", "CEO — company strategy and vision", "t4", None),
    ]);
    v
}
