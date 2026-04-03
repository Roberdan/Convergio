//! Agent prompt data — batch 2.

use super::seed_agents::AgentMeta;

const MARCUS_CONTEXT_MEMORY_KEEPER: &str =
    include_str!("../../data/agents/marcus-context-memory-keeper.md");
const PLAN_BUSINESS_ADVISOR: &str = include_str!("../../data/agents/plan-business-advisor.md");
const PLAN_POST_MORTEM: &str = include_str!("../../data/agents/plan-post-mortem.md");
const PLAN_REVIEWER: &str = include_str!("../../data/agents/plan-reviewer.md");
const PO_PROMPT_OPTIMIZER: &str = include_str!("../../data/agents/po-prompt-optimizer.md");
const SENTINEL_ECOSYSTEM_GUARDIAN: &str =
    include_str!("../../data/agents/sentinel-ecosystem-guardian.md");
const SOCRATES_FIRST_PRINCIPLES_REASONING: &str =
    include_str!("../../data/agents/socrates-first-principles-reasoning.md");
const STRATEGIC_PLANNER: &str = include_str!("../../data/agents/strategic-planner.md");
const TASKMASTER_STRATEGIC_TASK_DECOMPOSITION_MASTER: &str =
    include_str!("../../data/agents/taskmaster-strategic-task-decomposition-master.md");
const THOR_QUALITY_ASSURANCE_GUARDIAN: &str =
    include_str!("../../data/agents/thor-quality-assurance-guardian.md");
const WANDA_WORKFLOW_ORCHESTRATOR: &str =
    include_str!("../../data/agents/wanda-workflow-orchestrator.md");
const XAVIER_COORDINATION_PATTERNS: &str =
    include_str!("../../data/agents/xavier-coordination-patterns.md");
const JONY_CREATIVE_DIRECTOR: &str = include_str!("../../data/agents/jony-creative-director.md");
const NASRA_APP_BUILDER: &str = include_str!("../../data/agents/nasra-app-builder.md");
const SARA_UX_UI_DESIGNER: &str = include_str!("../../data/agents/sara-ux-ui-designer.md");
const STEFANO_DESIGN_THINKING_FACILITATOR: &str =
    include_str!("../../data/agents/stefano-design-thinking-facilitator.md");
const ALI_CHIEF_OF_STAFF: &str = include_str!("../../data/agents/ali-chief-of-staff.md");
const AMY_CFO: &str = include_str!("../../data/agents/amy-cfo.md");
const ANTONIO_STRATEGY_EXPERT: &str = include_str!("../../data/agents/antonio-strategy-expert.md");
const DAN_ENGINEERING_GM: &str = include_str!("../../data/agents/dan-engineering-gm.md");
const DOMIK_MCKINSEY_STRATEGIC_DECISION_MAKER: &str =
    include_str!("../../data/agents/domik-mckinsey-strategic-decision-maker.md");
const MATTEO_STRATEGIC_BUSINESS_ARCHITECT: &str =
    include_str!("../../data/agents/matteo-strategic-business-architect.md");
const SATYA_BOARD_OF_DIRECTORS: &str =
    include_str!("../../data/agents/satya-board-of-directors.md");
const APP_RELEASE_MANAGER_EXECUTION: &str =
    include_str!("../../data/agents/app-release-manager-execution.md");

pub static AGENTS: &[AgentMeta] = &[
    AgentMeta {
        name: "marcus-context-memory-keeper",
        category: "core_utility",
        model: "sonnet",
        max_turns: 15,
        tools: "",
        body: MARCUS_CONTEXT_MEMORY_KEEPER,
    },
    AgentMeta {
        name: "plan-business-advisor",
        category: "core_utility",
        model: "opus",
        max_turns: 20,
        tools: "",
        body: PLAN_BUSINESS_ADVISOR,
    },
    AgentMeta {
        name: "plan-post-mortem",
        category: "core_utility",
        model: "opus",
        max_turns: 30,
        tools: "",
        body: PLAN_POST_MORTEM,
    },
    AgentMeta {
        name: "plan-reviewer",
        category: "core_utility",
        model: "opus",
        max_turns: 25,
        tools: "",
        body: PLAN_REVIEWER,
    },
    AgentMeta {
        name: "po-prompt-optimizer",
        category: "core_utility",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: PO_PROMPT_OPTIMIZER,
    },
    AgentMeta {
        name: "sentinel-ecosystem-guardian",
        category: "core_utility",
        model: "opus",
        max_turns: 50,
        tools: "",
        body: SENTINEL_ECOSYSTEM_GUARDIAN,
    },
    AgentMeta {
        name: "socrates-first-principles-reasoning",
        category: "core_utility",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: SOCRATES_FIRST_PRINCIPLES_REASONING,
    },
    AgentMeta {
        name: "strategic-planner",
        category: "core_utility",
        model: "opus",
        max_turns: 40,
        tools: "",
        body: STRATEGIC_PLANNER,
    },
    AgentMeta {
        name: "taskmaster-strategic-task-decomposition-master",
        category: "core_utility",
        model: "haiku",
        max_turns: 20,
        tools: "",
        body: TASKMASTER_STRATEGIC_TASK_DECOMPOSITION_MASTER,
    },
    AgentMeta {
        name: "thor-quality-assurance-guardian",
        category: "core_utility",
        model: "sonnet",
        max_turns: 30,
        tools: "",
        body: THOR_QUALITY_ASSURANCE_GUARDIAN,
    },
    AgentMeta {
        name: "wanda-workflow-orchestrator",
        category: "core_utility",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: WANDA_WORKFLOW_ORCHESTRATOR,
    },
    AgentMeta {
        name: "xavier-coordination-patterns",
        category: "core_utility",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: XAVIER_COORDINATION_PATTERNS,
    },
    AgentMeta {
        name: "jony-creative-director",
        category: "design_ux",
        model: "sonnet",
        max_turns: 30,
        tools: "Read,Glob,Grep,WebSearch,WebFetch,Write,Edit",
        body: JONY_CREATIVE_DIRECTOR,
    },
    AgentMeta {
        name: "nasra-app-builder",
        category: "design_ux",
        model: "claude-sonnet-4-6",
        max_turns: 80,
        tools: "Read,Glob,Grep,Bash,Write,Edit,Task",
        body: NASRA_APP_BUILDER,
    },
    AgentMeta {
        name: "sara-ux-ui-designer",
        category: "design_ux",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: SARA_UX_UI_DESIGNER,
    },
    AgentMeta {
        name: "stefano-design-thinking-facilitator",
        category: "design_ux",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: STEFANO_DESIGN_THINKING_FACILITATOR,
    },
    AgentMeta {
        name: "ali-chief-of-staff",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 40,
        tools: "",
        body: ALI_CHIEF_OF_STAFF,
    },
    AgentMeta {
        name: "amy-cfo",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: AMY_CFO,
    },
    AgentMeta {
        name: "antonio-strategy-expert",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: ANTONIO_STRATEGY_EXPERT,
    },
    AgentMeta {
        name: "dan-engineering-gm",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: DAN_ENGINEERING_GM,
    },
    AgentMeta {
        name: "domik-mckinsey-strategic-decision-maker",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: DOMIK_MCKINSEY_STRATEGIC_DECISION_MAKER,
    },
    AgentMeta {
        name: "matteo-strategic-business-architect",
        category: "leadership_strategy",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: MATTEO_STRATEGIC_BUSINESS_ARCHITECT,
    },
    AgentMeta {
        name: "satya-board-of-directors",
        category: "leadership_strategy",
        model: "opus",
        max_turns: 30,
        tools: "",
        body: SATYA_BOARD_OF_DIRECTORS,
    },
    AgentMeta {
        name: "app-release-manager-execution",
        category: "release_management",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: APP_RELEASE_MANAGER_EXECUTION,
    },
];
