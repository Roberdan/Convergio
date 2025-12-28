"""
GraphFlow Workflow Definitions - Complete Business Process Library
Comprehensive business process definitions for Convergio AutoGen workflows covering
strategic analysis, product launches, market entry, and operational optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class WorkflowPriority(Enum):
    """Workflow execution priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StepType(Enum):
    """Types of workflow steps for proper execution handling"""
    ANALYSIS = "analysis"
    DECISION = "decision"
    RESEARCH = "research"
    PLANNING = "planning"
    COORDINATION = "coordination"
    VALIDATION = "validation"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    REPORTING = "reporting"


class BusinessDomain(Enum):
    """Business domains for workflow categorization"""
    STRATEGY = "strategy"
    OPERATIONS = "operations"
    FINANCE = "finance"
    MARKETING = "marketing"
    PRODUCT = "product"
    SALES = "sales"
    HR = "human_resources"
    TECHNOLOGY = "technology"
    LEGAL = "legal"
    COMPLIANCE = "compliance"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """Detailed workflow step definition with execution context"""
    step_id: str
    step_type: StepType
    agent_name: str
    description: str
    detailed_instructions: str
    inputs: List[str]
    outputs: List[str]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 2
    parallel_execution: bool = False
    approval_required: bool = False
    quality_gates: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    escalation_triggers: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    estimated_duration_minutes: int = 15
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class BusinessWorkflow:
    """Complete business workflow definition"""
    workflow_id: str
    name: str
    description: str
    business_domain: BusinessDomain
    priority: WorkflowPriority
    steps: List[WorkflowStep]
    entry_points: List[str]
    exit_conditions: Dict[str, str]
    success_metrics: Dict[str, str]
    failure_handling: Dict[str, str]
    escalation_rules: Dict[str, str]
    sla_minutes: int
    approval_gates: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Individual step execution result"""
    step_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    agent_response: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    escalated: bool = False
    approval_status: Optional[str] = None


@dataclass
class WorkflowExecution:
    """Enhanced workflow execution tracking"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    priority: WorkflowPriority
    current_step: Optional[str]
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    progress_percentage: float = 0.0
    user_id: str = ""
    session_id: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    cost_tracking: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def add_step_result(self, step_result: StepResult):
        """Add step execution result"""
        self.step_results[step_result.step_id] = step_result
        
        if step_result.status == "completed":
            if step_result.step_id not in self.completed_steps:
                self.completed_steps.append(step_result.step_id)
        elif step_result.status == "failed":
            if step_result.step_id not in self.failed_steps:
                self.failed_steps.append(step_result.step_id)
    
    def update_progress(self, total_steps: int):
        """Update progress percentage"""
        if total_steps > 0:
            self.progress_percentage = len(self.completed_steps) / total_steps * 100.0
    
    def is_sla_breached(self, sla_minutes: int) -> bool:
        """Check if SLA is breached"""
        if not self.start_time:
            return False
        elapsed = datetime.utcnow() - self.start_time
        return elapsed.total_seconds() > (sla_minutes * 60)


@dataclass
class WorkflowTemplate:
    """Workflow template for reusable business processes"""
    template_id: str
    name: str
    description: str
    business_domain: BusinessDomain
    use_cases: List[str]
    workflow_definition: BusinessWorkflow
    customization_parameters: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    success_stories: List[str] = field(default_factory=list)
    roi_metrics: Dict[str, str] = field(default_factory=dict)


# Pre-defined workflow templates for common business scenarios
STRATEGIC_ANALYSIS_TEMPLATE = WorkflowTemplate(
    template_id="strategic_analysis_v1",
    name="Strategic Analysis Framework",
    description="Comprehensive strategic analysis workflow for business planning",
    business_domain=BusinessDomain.STRATEGY,
    use_cases=[
        "Market opportunity analysis",
        "Competitive landscape assessment", 
        "Business model evaluation",
        "Strategic planning sessions"
    ],
    workflow_definition=BusinessWorkflow(
        workflow_id="strategic_analysis",
        name="Strategic Analysis Workflow",
        description="Multi-step strategic analysis with market research, competitive analysis, and strategic recommendations",
        business_domain=BusinessDomain.STRATEGY,
        priority=WorkflowPriority.HIGH,
        sla_minutes=180,  # 3 hours
        steps=[
            WorkflowStep(
                step_id="initial_context",
                step_type=StepType.RESEARCH,
                agent_name="socrates_first_principles_reasoning",
                description="Establish strategic context and fundamental assumptions",
                detailed_instructions="""
                Analyze the strategic context by:
                1. Identifying key business assumptions
                2. Questioning fundamental premises
                3. Establishing clear strategic objectives
                4. Defining success metrics
                5. Identifying potential blind spots
                """,
                inputs=["business_context", "strategic_question"],
                outputs=["strategic_context", "key_assumptions", "success_criteria"],
                estimated_duration_minutes=30
            ),
            WorkflowStep(
                step_id="market_analysis",
                step_type=StepType.ANALYSIS,
                agent_name="domik_mckinsey_strategic_decision_maker",
                description="Comprehensive market and competitive analysis",
                detailed_instructions="""
                Conduct thorough market analysis:
                1. Market size and growth potential
                2. Competitive landscape mapping
                3. Industry trend analysis
                4. Customer segmentation analysis
                5. Value chain analysis
                6. Porter's Five Forces assessment
                """,
                inputs=["strategic_context", "industry_data"],
                outputs=["market_insights", "competitive_analysis", "opportunity_map"],
                dependencies=["initial_context"],
                estimated_duration_minutes=60,
                tools_required=["market_research_api", "competitive_intel"]
            ),
            WorkflowStep(
                step_id="financial_analysis",
                step_type=StepType.ANALYSIS,
                agent_name="amy_cfo",
                description="Financial viability and investment analysis",
                detailed_instructions="""
                Perform comprehensive financial analysis:
                1. Revenue opportunity sizing
                2. Cost structure analysis
                3. Investment requirements
                4. ROI projections
                5. Risk assessment
                6. Sensitivity analysis
                """,
                inputs=["market_insights", "business_model"],
                outputs=["financial_projections", "investment_thesis", "risk_profile"],
                dependencies=["market_analysis"],
                estimated_duration_minutes=45,
                parallel_execution=True
            ),
            WorkflowStep(
                step_id="strategic_synthesis",
                step_type=StepType.DECISION,
                agent_name="ali_chief_of_staff",
                description="Synthesize insights into strategic recommendations",
                detailed_instructions="""
                Synthesize all analyses into actionable strategy:
                1. Integrate market, competitive, and financial insights
                2. Identify strategic options and trade-offs
                3. Develop implementation roadmap
                4. Define resource requirements
                5. Establish success metrics and milestones
                """,
                inputs=["market_insights", "competitive_analysis", "financial_projections"],
                outputs=["strategic_recommendations", "implementation_plan", "success_metrics"],
                dependencies=["market_analysis", "financial_analysis"],
                estimated_duration_minutes=45,
                approval_required=True
            )
        ],
        entry_points=["strategic_question", "business_context"],
        exit_conditions={
            "success": "strategic_recommendations_approved",
            "failure": "critical_analysis_gaps_identified"
        },
        success_metrics={
            "analysis_completeness": "All key areas analyzed with confidence > 0.8",
            "recommendation_clarity": "Clear, actionable recommendations provided",
            "stakeholder_alignment": "Key stakeholders aligned on strategic direction"
        },
        failure_handling={
            "data_gaps": "Escalate to research team for additional data collection",
            "analysis_conflicts": "Convene strategic review meeting",
            "timeline_breach": "Notify stakeholders and adjust scope"
        },
        escalation_rules={
            "high_uncertainty": "Escalate to CEO for strategic guidance",
            "resource_constraints": "Escalate to COO for resource allocation"
        },
        approval_gates=["strategic_synthesis"]
    ),
    prerequisites=["business_context_document", "market_data_access"],
    roi_metrics={
        "decision_speed": "50% faster strategic decisions",
        "analysis_quality": "90% stakeholder satisfaction with recommendations",
        "implementation_success": "80% of strategies successfully implemented"
    }
)


PRODUCT_LAUNCH_TEMPLATE = WorkflowTemplate(
    template_id="product_launch_v1", 
    name="Product Launch Framework",
    description="End-to-end product launch workflow with market validation",
    business_domain=BusinessDomain.PRODUCT,
    use_cases=[
        "New product launches",
        "Feature releases",
        "Market expansion",
        "Product repositioning"
    ],
    workflow_definition=BusinessWorkflow(
        workflow_id="product_launch",
        name="Product Launch Workflow",
        description="Comprehensive product launch with market validation, go-to-market strategy, and success tracking",
        business_domain=BusinessDomain.PRODUCT,
        priority=WorkflowPriority.CRITICAL,
        sla_minutes=480,  # 8 hours
        steps=[
            WorkflowStep(
                step_id="product_validation",
                step_type=StepType.VALIDATION,
                agent_name="socrates_first_principles_reasoning",
                description="Validate product concept and market fit",
                detailed_instructions="""
                Validate product opportunity:
                1. Product-market fit assessment
                2. Value proposition validation
                3. Target customer validation
                4. Competitive differentiation analysis
                5. Risk assessment
                """,
                inputs=["product_concept", "target_market"],
                outputs=["validation_results", "market_fit_score", "risk_assessment"],
                estimated_duration_minutes=60,
                quality_gates=["market_fit_score > 0.7"]
            ),
            WorkflowStep(
                step_id="gtm_strategy",
                step_type=StepType.PLANNING,
                agent_name="domik_mckinsey_strategic_decision_maker",
                description="Develop comprehensive go-to-market strategy",
                detailed_instructions="""
                Create go-to-market strategy:
                1. Market segmentation and targeting
                2. Positioning and messaging strategy
                3. Pricing strategy
                4. Channel strategy
                5. Launch timeline and milestones
                """,
                inputs=["validation_results", "competitive_landscape"],
                outputs=["gtm_strategy", "launch_timeline", "success_metrics"],
                dependencies=["product_validation"],
                estimated_duration_minutes=90
            ),
            WorkflowStep(
                step_id="financial_planning",
                step_type=StepType.PLANNING,
                agent_name="amy_cfo",
                description="Financial planning and budget allocation",
                detailed_instructions="""
                Develop financial plan:
                1. Revenue projections
                2. Cost structure analysis
                3. Marketing budget allocation
                4. ROI projections
                5. Break-even analysis
                """,
                inputs=["gtm_strategy", "market_size"],
                outputs=["financial_plan", "budget_allocation", "roi_projections"],
                dependencies=["gtm_strategy"],
                estimated_duration_minutes=60,
                parallel_execution=True
            ),
            WorkflowStep(
                step_id="execution_coordination",
                step_type=StepType.COORDINATION,
                agent_name="wanda_workflow_orchestrator",
                description="Coordinate cross-functional execution",
                detailed_instructions="""
                Coordinate launch execution:
                1. Team coordination and responsibilities
                2. Timeline synchronization
                3. Resource allocation
                4. Risk mitigation planning
                5. Communication plan
                """,
                inputs=["gtm_strategy", "financial_plan", "team_structure"],
                outputs=["execution_plan", "team_assignments", "communication_plan"],
                dependencies=["gtm_strategy", "financial_planning"],
                estimated_duration_minutes=45
            ),
            WorkflowStep(
                step_id="launch_monitoring",
                step_type=StepType.MONITORING,
                agent_name="diana_performance_dashboard",
                description="Set up launch monitoring and metrics tracking",
                detailed_instructions="""
                Establish monitoring framework:
                1. KPI dashboard setup
                2. Performance tracking mechanisms
                3. Feedback collection systems
                4. Real-time analytics
                5. Alert mechanisms
                """,
                inputs=["success_metrics", "execution_plan"],
                outputs=["monitoring_dashboard", "kpi_framework", "alert_system"],
                dependencies=["execution_coordination"],
                estimated_duration_minutes=30
            )
        ],
        entry_points=["product_concept", "target_market"],
        exit_conditions={
            "success": "launch_plan_approved_and_monitoring_active",
            "failure": "validation_failed_or_critical_gaps"
        },
        success_metrics={
            "validation_score": "Product validation score > 0.7",
            "plan_completeness": "All launch components defined and resourced",
            "timeline_feasibility": "Launch timeline achievable with current resources"
        },
        failure_handling={
            "validation_failure": "Return to product development for iteration",
            "resource_constraints": "Adjust scope or timeline",
            "market_changes": "Re-validate assumptions and adjust strategy"
        },
        escalation_rules={
            "budget_overrun": "Escalate to CFO for budget approval",
            "timeline_risk": "Escalate to CEO for priority adjustment"
        },
        approval_gates=["gtm_strategy", "financial_planning"]
    ),
    prerequisites=["product_specification", "competitive_analysis", "team_availability"],
    roi_metrics={
        "launch_success_rate": "85% of launches meet initial success criteria",
        "time_to_market": "30% reduction in launch timeline",
        "cross_functional_alignment": "95% team satisfaction with coordination"
    }
)


MARKET_ENTRY_TEMPLATE = WorkflowTemplate(
    template_id="market_entry_v1",
    name="Market Entry Strategy",
    description="Strategic market entry workflow for new geographical or segment expansion",
    business_domain=BusinessDomain.STRATEGY,
    use_cases=[
        "Geographic expansion",
        "New market segment entry",
        "International expansion",
        "Adjacent market entry"
    ],
    workflow_definition=BusinessWorkflow(
        workflow_id="market_entry",
        name="Market Entry Strategy Workflow", 
        description="Comprehensive market entry analysis with local market research and entry strategy development",
        business_domain=BusinessDomain.STRATEGY,
        priority=WorkflowPriority.HIGH,
        sla_minutes=360,  # 6 hours
        steps=[
            WorkflowStep(
                step_id="market_research",
                step_type=StepType.RESEARCH,
                agent_name="domik_mckinsey_strategic_decision_maker",
                description="Comprehensive target market research and analysis",
                detailed_instructions="""
                Conduct thorough market research:
                1. Market size and growth analysis
                2. Local competitive landscape
                3. Regulatory and compliance requirements
                4. Cultural and behavioral factors
                5. Economic and political stability
                """,
                inputs=["target_market", "entry_objectives"],
                outputs=["market_analysis", "competitive_landscape", "regulatory_requirements"],
                estimated_duration_minutes=90,
                tools_required=["market_research_api", "regulatory_database"]
            ),
            WorkflowStep(
                step_id="entry_strategy",
                step_type=StepType.PLANNING,
                agent_name="ali_chief_of_staff",
                description="Develop market entry strategy and approach",
                detailed_instructions="""
                Develop entry strategy:
                1. Entry mode selection (organic, acquisition, partnership)
                2. Localization requirements
                3. Partnership and alliance opportunities
                4. Resource requirements
                5. Timeline and milestones
                """,
                inputs=["market_analysis", "competitive_landscape", "company_capabilities"],
                outputs=["entry_strategy", "localization_plan", "partnership_opportunities"],
                dependencies=["market_research"],
                estimated_duration_minutes=75
            ),
            WorkflowStep(
                step_id="risk_assessment",
                step_type=StepType.ANALYSIS,
                agent_name="luca_security_expert",
                description="Comprehensive risk assessment and mitigation planning",
                detailed_instructions="""
                Assess market entry risks:
                1. Political and regulatory risks
                2. Economic and currency risks
                3. Competitive risks
                4. Operational risks
                5. Reputation risks
                """,
                inputs=["market_analysis", "entry_strategy"],
                outputs=["risk_assessment", "mitigation_strategies", "contingency_plans"],
                dependencies=["market_research"],
                estimated_duration_minutes=60,
                parallel_execution=True
            ),
            WorkflowStep(
                step_id="financial_modeling",
                step_type=StepType.ANALYSIS,
                agent_name="amy_cfo",
                description="Financial modeling and investment analysis",
                detailed_instructions="""
                Develop financial model:
                1. Investment requirements
                2. Revenue projections
                3. Cost structure analysis
                4. ROI and payback analysis
                5. Sensitivity analysis
                """,
                inputs=["market_analysis", "entry_strategy"],
                outputs=["financial_model", "investment_requirements", "roi_analysis"],
                dependencies=["entry_strategy"],
                estimated_duration_minutes=75
            ),
            WorkflowStep(
                step_id="implementation_planning",
                step_type=StepType.PLANNING,
                agent_name="wanda_workflow_orchestrator",
                description="Detailed implementation planning and execution roadmap",
                detailed_instructions="""
                Create implementation plan:
                1. Detailed project timeline
                2. Resource allocation and hiring plan
                3. Operational setup requirements
                4. Success metrics and monitoring
                5. Communication and stakeholder management
                """,
                inputs=["entry_strategy", "financial_model", "risk_assessment"],
                outputs=["implementation_plan", "resource_plan", "success_framework"],
                dependencies=["entry_strategy", "financial_modeling", "risk_assessment"],
                estimated_duration_minutes=60,
                approval_required=True
            )
        ],
        entry_points=["target_market", "entry_objectives"],
        exit_conditions={
            "success": "implementation_plan_approved",
            "failure": "market_entry_not_viable"
        },
        success_metrics={
            "market_attractiveness": "Market attractiveness score > 0.75",
            "financial_viability": "Projected ROI > company hurdle rate",
            "risk_acceptability": "Risk score within acceptable parameters"
        },
        failure_handling={
            "market_unviable": "Recommend alternative markets or timing",
            "regulatory_barriers": "Explore partnership or licensing options",
            "financial_unviable": "Adjust scope or entry mode"
        },
        escalation_rules={
            "high_investment": "Board approval required for >$10M investment",
            "high_risk": "Executive committee review required"
        },
        approval_gates=["implementation_planning"]
    ),
    prerequisites=["market_selection_criteria", "company_expansion_strategy", "investment_capacity"],
    roi_metrics={
        "entry_success_rate": "80% of entries meet 3-year targets",
        "planning_efficiency": "40% reduction in planning time",
        "risk_mitigation": "70% reduction in unforeseen market entry risks"
    }
)


