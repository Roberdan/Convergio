//! Agent prompt data — batch 1.

use super::seed_agents::AgentMeta;

const CEO: &str = include_str!("../../data/agents/ceo.md");
const PR_COMMENT_RESOLVER: &str = include_str!("../../data/agents/pr-comment-resolver.md");
const ANDREA_CUSTOMER_SUCCESS_MANAGER: &str =
    include_str!("../../data/agents/andrea-customer-success-manager.md");
const ANNA_EXECUTIVE_ASSISTANT: &str =
    include_str!("../../data/agents/anna-executive-assistant.md");
const DAVE_CHANGE_MANAGEMENT_SPECIALIST: &str =
    include_str!("../../data/agents/dave-change-management-specialist.md");
const DAVIDE_PROJECT_MANAGER: &str = include_str!("../../data/agents/davide-project-manager.md");
const ENRICO_BUSINESS_PROCESS_ENGINEER: &str =
    include_str!("../../data/agents/enrico-business-process-engineer.md");
const FABIO_SALES_BUSINESS_DEVELOPMENT: &str =
    include_str!("../../data/agents/fabio-sales-business-development.md");
const LUKE_PROGRAM_MANAGER: &str = include_str!("../../data/agents/luke-program-manager.md");
const MARCELLO_PM: &str = include_str!("../../data/agents/marcello-pm.md");
const SOFIA_MARKETING_STRATEGIST: &str =
    include_str!("../../data/agents/sofia-marketing-strategist.md");
const STEVE_EXECUTIVE_COMMUNICATION_STRATEGIST: &str =
    include_str!("../../data/agents/steve-executive-communication-strategist.md");
const DR_ENZO_HEALTHCARE_COMPLIANCE_MANAGER: &str =
    include_str!("../../data/agents/dr-enzo-healthcare-compliance-manager.md");
const ELENA_LEGAL_COMPLIANCE_EXPERT: &str =
    include_str!("../../data/agents/elena-legal-compliance-expert.md");
const GUARDIAN_AI_SECURITY_VALIDATOR: &str =
    include_str!("../../data/agents/guardian-ai-security-validator.md");
const LUCA_SECURITY_EXPERT: &str = include_str!("../../data/agents/luca-security-expert.md");
const SOPHIA_GOVAFFAIRS: &str = include_str!("../../data/agents/sophia-govaffairs.md");
const ALI_ORCHESTRATOR: &str = include_str!("../../data/agents/ali-orchestrator.md");
const COMPLIANCE_VALIDATOR: &str = include_str!("../../data/agents/compliance-validator.md");
const CONTEXT_OPTIMIZER: &str = include_str!("../../data/agents/context-optimizer.md");
const DEEP_REPO_AUDITOR: &str = include_str!("../../data/agents/deep-repo-auditor.md");
const DESIGN_VALIDATOR: &str = include_str!("../../data/agents/design-validator.md");
const DIANA_PERFORMANCE_DASHBOARD: &str =
    include_str!("../../data/agents/diana-performance-dashboard.md");
const DOC_VALIDATOR: &str = include_str!("../../data/agents/doc-validator.md");

pub static AGENTS: &[AgentMeta] = &[
    AgentMeta {
        name: "ceo",
        category: "core",
        model: "claude-opus-4.6",
        max_turns: 20,
        tools: "Read,Write,Edit,Bash,WebFetch",
        body: CEO,
    },
    AgentMeta {
        name: "pr-comment-resolver",
        category: "core",
        model: "sonnet",
        max_turns: 20,
        tools: "Read,Edit,Write,Bash,Glob,Grep",
        body: PR_COMMENT_RESOLVER,
    },
    AgentMeta {
        name: "andrea-customer-success-manager",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: ANDREA_CUSTOMER_SUCCESS_MANAGER,
    },
    AgentMeta {
        name: "anna-executive-assistant",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: ANNA_EXECUTIVE_ASSISTANT,
    },
    AgentMeta {
        name: "dave-change-management-specialist",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: DAVE_CHANGE_MANAGEMENT_SPECIALIST,
    },
    AgentMeta {
        name: "davide-project-manager",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: DAVIDE_PROJECT_MANAGER,
    },
    AgentMeta {
        name: "enrico-business-process-engineer",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: ENRICO_BUSINESS_PROCESS_ENGINEER,
    },
    AgentMeta {
        name: "fabio-sales-business-development",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: FABIO_SALES_BUSINESS_DEVELOPMENT,
    },
    AgentMeta {
        name: "luke-program-manager",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: LUKE_PROGRAM_MANAGER,
    },
    AgentMeta {
        name: "marcello-pm",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: MARCELLO_PM,
    },
    AgentMeta {
        name: "sofia-marketing-strategist",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: SOFIA_MARKETING_STRATEGIST,
    },
    AgentMeta {
        name: "steve-executive-communication-strategist",
        category: "business_operations",
        model: "haiku",
        max_turns: 15,
        tools: "",
        body: STEVE_EXECUTIVE_COMMUNICATION_STRATEGIST,
    },
    AgentMeta {
        name: "dr-enzo-healthcare-compliance-manager",
        category: "compliance_legal",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: DR_ENZO_HEALTHCARE_COMPLIANCE_MANAGER,
    },
    AgentMeta {
        name: "elena-legal-compliance-expert",
        category: "compliance_legal",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: ELENA_LEGAL_COMPLIANCE_EXPERT,
    },
    AgentMeta {
        name: "guardian-ai-security-validator",
        category: "compliance_legal",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: GUARDIAN_AI_SECURITY_VALIDATOR,
    },
    AgentMeta {
        name: "luca-security-expert",
        category: "compliance_legal",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: LUCA_SECURITY_EXPERT,
    },
    AgentMeta {
        name: "sophia-govaffairs",
        category: "compliance_legal",
        model: "sonnet",
        max_turns: 20,
        tools: "",
        body: SOPHIA_GOVAFFAIRS,
    },
    AgentMeta {
        name: "ali-orchestrator",
        category: "core_utility",
        model: "opus",
        max_turns: 100,
        tools: "copilot",
        body: ALI_ORCHESTRATOR,
    },
    AgentMeta {
        name: "compliance-validator",
        category: "core_utility",
        model: "opus",
        max_turns: 20,
        tools: "",
        body: COMPLIANCE_VALIDATOR,
    },
    AgentMeta {
        name: "context-optimizer",
        category: "core_utility",
        model: "opus",
        max_turns: 50,
        tools: "",
        body: CONTEXT_OPTIMIZER,
    },
    AgentMeta {
        name: "deep-repo-auditor",
        category: "core_utility",
        model: "opus",
        max_turns: 50,
        tools: "Read,Write,Edit,Bash,Glob,Grep,Task",
        body: DEEP_REPO_AUDITOR,
    },
    AgentMeta {
        name: "design-validator",
        category: "core_utility",
        model: "sonnet",
        max_turns: 20,
        tools: "copilot",
        body: DESIGN_VALIDATOR,
    },
    AgentMeta {
        name: "diana-performance-dashboard",
        category: "core_utility",
        model: "sonnet",
        max_turns: 15,
        tools: "",
        body: DIANA_PERFORMANCE_DASHBOARD,
    },
    AgentMeta {
        name: "doc-validator",
        category: "core_utility",
        model: "sonnet",
        max_turns: 20,
        tools: "copilot",
        body: DOC_VALIDATOR,
    },
];
