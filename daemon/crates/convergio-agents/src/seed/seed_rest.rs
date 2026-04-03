//! Seed data: compliance, specialized, design, release, research (22 agents).

use crate::types::{AgentCategory, AgentInput};

fn ag(name: &str, role: &str, cat: AgentCategory, tier: &str, esc: Option<&str>) -> AgentInput {
    AgentInput {
        name: name.into(),
        role: role.into(),
        org: "convergio".into(),
        category: cat,
        model_tier: tier.into(),
        max_tokens: 200_000,
        hourly_budget: 0.0,
        capabilities: vec![],
        prompt_ref: None,
        escalation_target: esc.map(Into::into),
    }
}

pub fn agents() -> Vec<AgentInput> {
    use AgentCategory::*;
    vec![
        // compliance_legal (5)
        ag(
            "elena",
            "Compliance officer — GDPR, legal review",
            ComplianceLegal,
            "t3",
            Some("ali-orchestrator"),
        ),
        ag(
            "luca",
            "Legal counsel — contracts and IP",
            ComplianceLegal,
            "t3",
            Some("elena"),
        ),
        ag(
            "guardian",
            "Security guardian — access and secrets",
            ComplianceLegal,
            "t3",
            Some("sentinel"),
        ),
        ag(
            "dr-enzo",
            "Ethics advisor — AI alignment",
            ComplianceLegal,
            "t3",
            Some("ali-orchestrator"),
        ),
        ag(
            "sophia",
            "Privacy engineer — data minimization",
            ComplianceLegal,
            "t2",
            Some("elena"),
        ),
        // specialized_experts (7)
        ag(
            "fiona",
            "Database expert — schema and query optimization",
            SpecializedExperts,
            "t3",
            Some("baccio"),
        ),
        ag(
            "sam",
            "Infra specialist — networking and deployment",
            SpecializedExperts,
            "t3",
            Some("marco-devops"),
        ),
        ag(
            "wiz",
            "API wizard — design and integration expert",
            SpecializedExperts,
            "t3",
            Some("baccio"),
        ),
        ag(
            "behice",
            "Testing expert — strategy and automation",
            SpecializedExperts,
            "t3",
            Some("thor"),
        ),
        ag(
            "coach",
            "Developer coach — mentoring and onboarding",
            SpecializedExperts,
            "t2",
            Some("ali-orchestrator"),
        ),
        ag(
            "giulia",
            "Localization expert — i18n and l10n",
            SpecializedExperts,
            "t2",
            Some("ali-orchestrator"),
        ),
        ag(
            "jenny",
            "AI prompt engineer — prompt crafting",
            SpecializedExperts,
            "t3",
            Some("ali-orchestrator"),
        ),
        // design_ux (4)
        ag(
            "jony",
            "Chief designer — UI/UX vision",
            DesignUx,
            "t3",
            Some("matteo"),
        ),
        ag(
            "sara",
            "UX researcher — user testing and flows",
            DesignUx,
            "t2",
            Some("jony"),
        ),
        ag(
            "nasra",
            "Visual designer — brand and components",
            DesignUx,
            "t2",
            Some("jony"),
        ),
        ag(
            "stefano",
            "Frontend architect — design system impl",
            DesignUx,
            "t3",
            Some("jony"),
        ),
        // release_management (5)
        ag(
            "app-release-manager-ios",
            "iOS app release manager",
            ReleaseManagement,
            "t2",
            Some("marco-devops"),
        ),
        ag(
            "app-release-manager-android",
            "Android app release manager",
            ReleaseManagement,
            "t2",
            Some("marco-devops"),
        ),
        ag(
            "ecosystem-sync",
            "Ecosystem sync — cross-repo coordination",
            ReleaseManagement,
            "t2",
            Some("ali-orchestrator"),
        ),
        ag(
            "feature-release-manager",
            "Feature flag and rollout manager",
            ReleaseManagement,
            "t2",
            Some("marco-devops"),
        ),
        ag(
            "mirrorbuddy",
            "Mirror buddy — fork and sync management",
            ReleaseManagement,
            "t1",
            Some("marco-devops"),
        ),
        // research_report (1)
        ag(
            "research-report-generator",
            "Generates structured research reports",
            ResearchReport,
            "t3",
            Some("ali-orchestrator"),
        ),
    ]
}
