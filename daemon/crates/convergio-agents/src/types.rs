//! Core types for the agent catalog.

use serde::{Deserialize, Serialize};

/// Classification of agents into functional categories.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AgentCategory {
    CoreUtility,
    TechnicalDevelopment,
    BusinessOperations,
    LeadershipStrategy,
    ComplianceLegal,
    SpecializedExperts,
    DesignUx,
    ReleaseManagement,
    ResearchReport,
}

impl AgentCategory {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::CoreUtility => "core_utility",
            Self::TechnicalDevelopment => "technical_development",
            Self::BusinessOperations => "business_operations",
            Self::LeadershipStrategy => "leadership_strategy",
            Self::ComplianceLegal => "compliance_legal",
            Self::SpecializedExperts => "specialized_experts",
            Self::DesignUx => "design_ux",
            Self::ReleaseManagement => "release_management",
            Self::ResearchReport => "research_report",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "core_utility" => Some(Self::CoreUtility),
            "technical_development" => Some(Self::TechnicalDevelopment),
            "business_operations" => Some(Self::BusinessOperations),
            "leadership_strategy" => Some(Self::LeadershipStrategy),
            "compliance_legal" => Some(Self::ComplianceLegal),
            "specialized_experts" => Some(Self::SpecializedExperts),
            "design_ux" => Some(Self::DesignUx),
            "release_management" => Some(Self::ReleaseManagement),
            "research_report" => Some(Self::ResearchReport),
            _ => None,
        }
    }
}

impl std::fmt::Display for AgentCategory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Catalog entry status.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AgentStatus {
    Active,
    Disabled,
    Deprecated,
}

impl AgentStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Active => "active",
            Self::Disabled => "disabled",
            Self::Deprecated => "deprecated",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        match s {
            "active" => Some(Self::Active),
            "disabled" => Some(Self::Disabled),
            "deprecated" => Some(Self::Deprecated),
            _ => None,
        }
    }
}

/// Full agent specification — what the daemon needs to spawn an agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSpec {
    pub id: String,
    pub name: String,
    pub role: String,
    pub org: String,
    pub category: AgentCategory,
    /// Model tier preference: t1 (cheapest) to t4 (most capable).
    pub model_tier: String,
    pub max_tokens: i64,
    pub hourly_budget: f64,
    pub capabilities: Vec<String>,
    /// UUID of the prompt template in convergio-prompts.
    pub prompt_ref: Option<String>,
    /// Agent to escalate to when stuck or over budget.
    pub escalation_target: Option<String>,
    pub status: AgentStatus,
    pub created_at: String,
    pub updated_at: String,
}

/// Input for creating/updating an agent spec.
#[derive(Debug, Clone, Deserialize)]
pub struct AgentInput {
    pub name: String,
    pub role: String,
    #[serde(default = "default_org")]
    pub org: String,
    pub category: AgentCategory,
    #[serde(default = "default_tier")]
    pub model_tier: String,
    #[serde(default = "default_max_tokens")]
    pub max_tokens: i64,
    #[serde(default)]
    pub hourly_budget: f64,
    #[serde(default)]
    pub capabilities: Vec<String>,
    pub prompt_ref: Option<String>,
    pub escalation_target: Option<String>,
}

fn default_org() -> String {
    "convergio".into()
}
fn default_tier() -> String {
    "t2".into()
}
fn default_max_tokens() -> i64 {
    200_000
}

/// Query filters for listing agents.
#[derive(Debug, Clone, Deserialize, Default)]
pub struct AgentQuery {
    pub category: Option<String>,
    pub status: Option<String>,
    pub name: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn category_roundtrip() {
        for cat in [
            AgentCategory::CoreUtility,
            AgentCategory::TechnicalDevelopment,
            AgentCategory::DesignUx,
            AgentCategory::ResearchReport,
        ] {
            let s = cat.as_str();
            assert_eq!(AgentCategory::parse(s), Some(cat));
        }
    }

    #[test]
    fn status_roundtrip() {
        for st in [AgentStatus::Active, AgentStatus::Disabled] {
            assert_eq!(AgentStatus::parse(st.as_str()), Some(st));
        }
    }

    #[test]
    fn category_display() {
        assert_eq!(AgentCategory::CoreUtility.to_string(), "core_utility");
    }
}
