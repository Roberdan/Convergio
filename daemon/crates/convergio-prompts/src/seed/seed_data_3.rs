//! Agent prompt data — batch 3.

use super::seed_agents::AgentMeta;

const APP_RELEASE_MANAGER: &str = include_str!("../../data/agents/app-release-manager.md");
const ECOSYSTEM_SYNC: &str = include_str!("../../data/agents/ecosystem-sync.md");
const FEATURE_RELEASE_MANAGER: &str = include_str!("../../data/agents/feature-release-manager.md");
const MIRRORBUDDY_HARDENING_CHECKS: &str =
    include_str!("../../data/agents/mirrorbuddy-hardening-checks.md");
const RESEARCH_REPORT_GENERATOR: &str =
    include_str!("../../data/agents/research-report-generator.md");
const BEHICE_CULTURAL_COACH: &str = include_str!("../../data/agents/behice-cultural-coach.md");
const COACH_TEAM_COACH: &str = include_str!("../../data/agents/coach-team-coach.md");
const FIONA_MARKET_ANALYST: &str = include_str!("../../data/agents/fiona-market-analyst.md");
const GIULIA_HR_TALENT_ACQUISITION: &str =
    include_str!("../../data/agents/giulia-hr-talent-acquisition.md");
const JENNY_INCLUSIVE_ACCESSIBILITY_CHAMPION: &str =
    include_str!("../../data/agents/jenny-inclusive-accessibility-champion.md");
const SAM_STARTUPPER: &str = include_str!("../../data/agents/sam-startupper.md");
const WIZ_INVESTOR_VENTURE_CAPITAL: &str =
    include_str!("../../data/agents/wiz-investor-venture-capital.md");
const ADVERSARIAL_DEBUGGER: &str = include_str!("../../data/agents/adversarial-debugger.md");
const BACCIO_TECH_ARCHITECT: &str = include_str!("../../data/agents/baccio-tech-architect.md");
const DARIO_DEBUGGER: &str = include_str!("../../data/agents/dario-debugger.md");
const MARCO_DEVOPS_ENGINEER: &str = include_str!("../../data/agents/marco-devops-engineer.md");
const OMRI_DATA_SCIENTIST: &str = include_str!("../../data/agents/omri-data-scientist.md");
const OTTO_PERFORMANCE_OPTIMIZER: &str =
    include_str!("../../data/agents/otto-performance-optimizer.md");
const PAOLO_BEST_PRACTICES_ENFORCER: &str =
    include_str!("../../data/agents/paolo-best-practices-enforcer.md");
const REX_CODE_REVIEWER: &str = include_str!("../../data/agents/rex-code-reviewer.md");
const TASK_EXECUTOR_TDD: &str = include_str!("../../data/agents/task-executor-tdd.md");
const TASK_EXECUTOR: &str = include_str!("../../data/agents/task-executor.md");

pub static AGENTS: &[AgentMeta] = &[
    AgentMeta {
        name: "app-release-manager",
        category: "release_management",
        model: "sonnet",
        max_turns: 40,
        tools: "",
        body: APP_RELEASE_MANAGER,
    },
    AgentMeta {
        name: "ecosystem-sync",
        category: "release_management",
        model: "sonnet",
        max_turns: 30,
        tools: "",
        body: ECOSYSTEM_SYNC,
    },
    AgentMeta {
        name: "feature-release-manager",
        category: "release_management",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: FEATURE_RELEASE_MANAGER,
    },
    AgentMeta {
        name: "mirrorbuddy-hardening-checks",
        category: "release_management",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: MIRRORBUDDY_HARDENING_CHECKS,
    },
    AgentMeta {
        name: "research-report-generator",
        category: "research_report",
        model: "opus",
        max_turns: 50,
        tools: "",
        body: RESEARCH_REPORT_GENERATOR,
    },
    AgentMeta {
        name: "behice-cultural-coach",
        category: "specialized_experts",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: BEHICE_CULTURAL_COACH,
    },
    AgentMeta {
        name: "coach-team-coach",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: COACH_TEAM_COACH,
    },
    AgentMeta {
        name: "fiona-market-analyst",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: FIONA_MARKET_ANALYST,
    },
    AgentMeta {
        name: "giulia-hr-talent-acquisition",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: GIULIA_HR_TALENT_ACQUISITION,
    },
    AgentMeta {
        name: "jenny-inclusive-accessibility-champion",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: JENNY_INCLUSIVE_ACCESSIBILITY_CHAMPION,
    },
    AgentMeta {
        name: "sam-startupper",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: SAM_STARTUPPER,
    },
    AgentMeta {
        name: "wiz-investor-venture-capital",
        category: "specialized_experts",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: WIZ_INVESTOR_VENTURE_CAPITAL,
    },
    AgentMeta {
        name: "adversarial-debugger",
        category: "technical_development",
        model: "sonnet",
        max_turns: 25,
        tools: "",
        body: ADVERSARIAL_DEBUGGER,
    },
    AgentMeta {
        name: "baccio-tech-architect",
        category: "technical_development",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: BACCIO_TECH_ARCHITECT,
    },
    AgentMeta {
        name: "dario-debugger",
        category: "technical_development",
        model: "sonnet",
        max_turns: 15,
        tools: "",
        body: DARIO_DEBUGGER,
    },
    AgentMeta {
        name: "marco-devops-engineer",
        category: "technical_development",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: MARCO_DEVOPS_ENGINEER,
    },
    AgentMeta {
        name: "omri-data-scientist",
        category: "technical_development",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: OMRI_DATA_SCIENTIST,
    },
    AgentMeta {
        name: "otto-performance-optimizer",
        category: "technical_development",
        model: "sonnet",
        max_turns: 15,
        tools: "",
        body: OTTO_PERFORMANCE_OPTIMIZER,
    },
    AgentMeta {
        name: "paolo-best-practices-enforcer",
        category: "technical_development",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: PAOLO_BEST_PRACTICES_ENFORCER,
    },
    AgentMeta {
        name: "rex-code-reviewer",
        category: "technical_development",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: REX_CODE_REVIEWER,
    },
    AgentMeta {
        name: "task-executor-tdd",
        category: "technical_development",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: TASK_EXECUTOR_TDD,
    },
    AgentMeta {
        name: "task-executor",
        category: "technical_development",
        model: "sonnet",
        max_turns: 50,
        tools: "",
        body: TASK_EXECUTOR,
    },
];
