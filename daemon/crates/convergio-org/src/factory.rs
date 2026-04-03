//! Org factory — designs an org structure from a mission statement or repo profile.

use serde::{Deserialize, Serialize};

use super::repo_scanner::RepoProfile;

/// Complete blueprint for an organisation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrgBlueprint {
    pub name: String,
    pub slug: String,
    pub mission: String,
    pub repo_path: Option<String>,
    pub budget_usd: Option<f64>,
    pub ceo_agent: String,
    pub departments: Vec<Department>,
    pub night_agents: Vec<NightAgentSpec>,
}

/// A department within the org containing one or more agents.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Department {
    pub name: String,
    pub agents: Vec<AgentSpec>,
}

/// Specification for a single agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSpec {
    pub name: String,
    pub model: String,
    pub capabilities: Vec<String>,
}

/// Specification for a night (off-peak) agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NightAgentSpec {
    pub name: String,
    pub schedule: String,
    pub time: String,
    pub model: String,
}

const MODEL_SONNET: &str = "claude-sonnet-4-5";
const MODEL_HAIKU: &str = "claude-haiku-4-5";

/// Convert a name to a URL-safe slug (lowercase, alphanumeric + hyphens).
pub fn slugify(name: &str) -> String {
    let mut slug = String::with_capacity(name.len());
    let mut prev_dash = true;
    for ch in name.chars() {
        if ch.is_ascii_alphanumeric() {
            slug.push(ch.to_ascii_lowercase());
            prev_dash = false;
        } else if !prev_dash {
            slug.push('-');
            prev_dash = true;
        }
    }
    if slug.ends_with('-') {
        slug.pop();
    }
    slug
}

/// Design an org from a mission statement (rule-based, no LLM call).
pub fn design_org_from_mission(name: &str, mission: &str, budget: f64) -> OrgBlueprint {
    let slug = slugify(name);
    let lower = mission.to_lowercase();
    let departments = mission_departments(&lower, &slug);
    let night_agents = mission_night_agents(&lower, &slug);
    OrgBlueprint {
        name: name.to_string(),
        slug: slug.clone(),
        mission: mission.to_string(),
        ceo_agent: format!("{slug}-ceo"),
        departments,
        night_agents,
        repo_path: None,
        budget_usd: Some(budget),
    }
}

/// Design an org by mapping a scanned repo profile to departments.
pub fn design_org_from_repo(
    profile: &RepoProfile,
    name: Option<&str>,
    budget: f64,
) -> OrgBlueprint {
    let repo_name = name.unwrap_or_else(|| {
        profile.path.rsplit('/').find(|s| !s.is_empty()).unwrap_or("org")
    });
    let slug = slugify(repo_name);
    let departments = repo_departments(profile, &slug);
    let night_agents = repo_night_agents(profile, &slug);
    OrgBlueprint {
        name: repo_name.to_string(),
        slug: slug.clone(),
        mission: format!("Maintain and evolve {repo_name}"),
        ceo_agent: format!("{slug}-ceo"),
        departments,
        night_agents,
        repo_path: Some(profile.path.clone()),
        budget_usd: Some(budget),
    }
}

fn mission_departments(lower: &str, slug: &str) -> Vec<Department> {
    let kw_fit = ["fitness", "health", "training", "workout", "gym"];
    let kw_sw = ["software", "code", "app", "platform", "saas"];
    let kw_mkt = ["marketing", "sales", "growth", "ads", "campaign"];

    if kw_fit.iter().any(|k| lower.contains(k)) {
        vec![
            dept(slug, "Nutrition", &[("nutritionist", MODEL_SONNET, "meal planning")]),
            dept(slug, "Training", &[
                ("trainer", MODEL_SONNET, "workout programming"),
                ("form-checker", MODEL_HAIKU, "exercise form review"),
            ]),
            dept(slug, "Analytics", &[("analyst", MODEL_HAIKU, "progress tracking")]),
        ]
    } else if kw_sw.iter().any(|k| lower.contains(k)) {
        vec![
            dept(slug, "Development", &[("lead-dev", MODEL_SONNET, "architecture")]),
            dept(slug, "QA", &[("tester", MODEL_HAIKU, "testing")]),
            dept(slug, "DevOps", &[("ci-ops", MODEL_HAIKU, "CI/CD")]),
        ]
    } else if kw_mkt.iter().any(|k| lower.contains(k)) {
        vec![
            dept(slug, "Marketing", &[("strategist", MODEL_SONNET, "campaign strategy")]),
            dept(slug, "Analytics", &[("data-analyst", MODEL_HAIKU, "metrics")]),
            dept(slug, "Content", &[("writer", MODEL_SONNET, "copywriting")]),
        ]
    } else {
        vec![
            dept(slug, "Strategy", &[("strategist", MODEL_SONNET, "planning")]),
            dept(slug, "Execution", &[("executor", MODEL_SONNET, "task execution")]),
            dept(slug, "Analytics", &[("analyst", MODEL_HAIKU, "data analysis")]),
        ]
    }
}

fn mission_night_agents(lower: &str, slug: &str) -> Vec<NightAgentSpec> {
    let mut agents = vec![night(slug, "daily-report", "daily_report", "0 2 * * *")];
    if lower.contains("software") || lower.contains("code") || lower.contains("app") {
        agents.push(night(slug, "pr-monitor", "monitor_prs", "*/30 0-6 * * *"));
        agents.push(night(slug, "dep-updater", "dep_update", "0 5 * * 1"));
    }
    if lower.contains("marketing") || lower.contains("sales") {
        agents.push(night(slug, "metrics-digest", "daily_report", "0 3 * * *"));
    }
    agents
}

fn repo_departments(profile: &RepoProfile, slug: &str) -> Vec<Department> {
    let mut depts = Vec::new();
    let langs: Vec<String> = profile.languages.iter().map(|(l, _)| l.to_lowercase()).collect();
    if langs.iter().any(|l| l == "rust") {
        depts.push(dept(slug, "Backend", &[
            ("rust-dev", MODEL_SONNET, "Rust development"),
            ("clippy-reviewer", MODEL_HAIKU, "Rust lint review"),
        ]));
    }
    if langs.iter().any(|l| l == "typescript" || l == "javascript") {
        depts.push(dept(slug, "Frontend", &[
            ("component-dev", MODEL_SONNET, "UI components"),
            ("design-reviewer", MODEL_HAIKU, "design review"),
        ]));
    }
    if langs.iter().any(|l| l == "python") {
        depts.push(dept(slug, "Backend", &[
            ("python-dev", MODEL_SONNET, "Python development"),
            ("test-runner", MODEL_HAIKU, "test execution"),
        ]));
    }
    if profile.structure.has_ci {
        depts.push(dept(slug, "DevOps", &[("ci-monitor", MODEL_HAIKU, "CI monitoring")]));
    }
    if profile.structure.has_tests {
        depts.push(dept(slug, "QA", &[("test-runner", MODEL_HAIKU, "test management")]));
    }
    if depts.is_empty() {
        depts.push(dept(slug, "General", &[("dev", MODEL_SONNET, "general development")]));
    }
    depts
}

fn repo_night_agents(profile: &RepoProfile, slug: &str) -> Vec<NightAgentSpec> {
    let mut agents = vec![
        night(slug, "daily-report", "daily_report", "0 2 * * *"),
        night(slug, "stale-branch-cleanup", "stale_branch_cleanup", "0 3 * * *"),
    ];
    if profile.structure.has_ci {
        agents.push(night(slug, "pr-monitor", "monitor_prs", "*/30 0-6 * * *"));
        agents.push(night(slug, "coverage-check", "test_coverage", "0 4 * * *"));
    }
    if !profile.dependencies.is_empty() {
        agents.push(night(slug, "dep-updater", "dependency_update", "0 5 * * 1"));
    }
    agents
}

fn dept(slug: &str, name: &str, agents: &[(&str, &str, &str)]) -> Department {
    Department {
        name: name.to_string(),
        agents: agents
            .iter()
            .map(|(aname, model, cap)| AgentSpec {
                name: format!("{slug}-{aname}"),
                model: model.to_string(),
                capabilities: vec![cap.to_string()],
            })
            .collect(),
    }
}

fn night(slug: &str, suffix: &str, task: &str, schedule: &str) -> NightAgentSpec {
    NightAgentSpec {
        name: format!("{slug}-{suffix}"),
        schedule: task.to_string(),
        time: schedule.to_string(),
        model: MODEL_HAIKU.to_string(),
    }
}
