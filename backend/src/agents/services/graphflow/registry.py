"""
GraphFlow Registry - Complete Workflow Library and Management System
Comprehensive registry for business workflows with template management,
customization, and dynamic workflow generation capabilities.
"""

from typing import Dict, List, Optional, Any
from dataclasses import asdict, dataclass

import structlog

from .definitions import (
    BusinessWorkflow,
    WorkflowStep,
    WorkflowTemplate,
    BusinessDomain,
    WorkflowPriority,
    StepType,
    STRATEGIC_ANALYSIS_TEMPLATE,
    PRODUCT_LAUNCH_TEMPLATE,
    MARKET_ENTRY_TEMPLATE,
)

logger = structlog.get_logger()


@dataclass
class WorkflowCatalogEntry:
    """Workflow catalog entry with metadata"""
    workflow_id: str
    name: str
    description: str
    category: str
    business_domain: BusinessDomain
    complexity: str
    estimated_duration_minutes: int
    steps_count: int
    success_rate: float
    avg_completion_time_minutes: int
    usage_count: int
    tags: List[str]
    prerequisites: List[str]
    roi_metrics: Dict[str, str]


class ComprehensiveWorkflowRegistry:
    """Complete workflow registry with template management and customization"""
    
    def __init__(self):
        self.workflows: Dict[str, BusinessWorkflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.catalog: List[WorkflowCatalogEntry] = []
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize registry with pre-defined templates and workflows"""
        
        # Load pre-defined templates
        self._load_predefined_templates()
        
        # Generate workflows from templates
        self._generate_workflows_from_templates()
        
        # Build catalog
        self._build_workflow_catalog()
        
        # Initialize usage statistics
        self._initialize_usage_stats()
    
    def _load_predefined_templates(self):
        """Load pre-defined workflow templates"""
        
        templates = {
            STRATEGIC_ANALYSIS_TEMPLATE.template_id: STRATEGIC_ANALYSIS_TEMPLATE,
            PRODUCT_LAUNCH_TEMPLATE.template_id: PRODUCT_LAUNCH_TEMPLATE,
            MARKET_ENTRY_TEMPLATE.template_id: MARKET_ENTRY_TEMPLATE
        }
        
        # Add additional operational templates
        templates.update(self._create_operational_templates())
        
        self.templates = templates
        
        logger.info(f"Loaded {len(templates)} workflow templates", templates=list(templates.keys()))
    
    def _create_operational_templates(self) -> Dict[str, WorkflowTemplate]:
        """Create additional operational workflow templates"""
        
        # Customer Onboarding Template
        customer_onboarding = WorkflowTemplate(
            template_id="customer_onboarding_v1",
            name="Customer Onboarding Framework",
            description="Streamlined customer onboarding with success tracking",
            business_domain=BusinessDomain.OPERATIONS,
            use_cases=[
                "New customer onboarding",
                "Enterprise client setup",
                "Customer success optimization",
                "Retention improvement"
            ],
            workflow_definition=BusinessWorkflow(
                workflow_id="customer_onboarding",
                name="Customer Onboarding Workflow",
                description="Comprehensive customer onboarding with personalization and success tracking",
                business_domain=BusinessDomain.OPERATIONS,
                priority=WorkflowPriority.HIGH,
                sla_minutes=240,  # 4 hours
                steps=[
                    WorkflowStep(
                        step_id="customer_profiling",
                        step_type=StepType.ANALYSIS,
                        agent_name="domik_mckinsey_strategic_decision_maker",
                        description="Customer needs analysis and segmentation",
                        detailed_instructions="""
                        Analyze customer profile:
                        1. Business needs assessment
                        2. Use case identification
                        3. Success criteria definition
                        4. Risk factors evaluation
                        5. Customization requirements
                        """,
                        inputs=["customer_data", "business_requirements"],
                        outputs=["customer_profile", "success_criteria", "customization_needs"],
                        estimated_duration_minutes=45
                    ),
                    WorkflowStep(
                        step_id="onboarding_plan",
                        step_type=StepType.PLANNING,
                        agent_name="wanda_workflow_orchestrator",
                        description="Personalized onboarding plan creation",
                        detailed_instructions="""
                        Create onboarding plan:
                        1. Milestone-based timeline
                        2. Resource allocation
                        3. Training requirements
                        4. Integration checkpoints
                        5. Success measurement plan
                        """,
                        inputs=["customer_profile", "service_capabilities"],
                        outputs=["onboarding_plan", "training_schedule", "success_metrics"],
                        dependencies=["customer_profiling"],
                        estimated_duration_minutes=60
                    ),
                    WorkflowStep(
                        step_id="execution_monitoring",
                        step_type=StepType.MONITORING,
                        agent_name="diana_performance_dashboard",
                        description="Onboarding execution and progress tracking",
                        detailed_instructions="""
                        Monitor onboarding progress:
                        1. Milestone completion tracking
                        2. Customer satisfaction monitoring
                        3. Issue identification and resolution
                        4. Success metrics measurement
                        5. Optimization recommendations
                        """,
                        inputs=["onboarding_plan", "execution_data"],
                        outputs=["progress_report", "satisfaction_score", "optimization_recommendations"],
                        dependencies=["onboarding_plan"],
                        estimated_duration_minutes=30
                    )
                ],
                entry_points=["customer_data", "business_requirements"],
                exit_conditions={
                    "success": "customer_successfully_onboarded",
                    "failure": "onboarding_requirements_not_met"
                },
                success_metrics={
                    "completion_rate": "95% of onboarding milestones completed",
                    "satisfaction_score": "Customer satisfaction > 4.5/5.0",
                    "time_to_value": "Customer achieves value within defined timeline"
                },
                failure_handling={
                    "timeline_delays": "Adjust timeline and notify stakeholders",
                    "technical_issues": "Escalate to technical support team",
                    "satisfaction_issues": "Schedule customer success review"
                },
                escalation_rules={
                    "critical_issues": "Escalate to customer success manager",
                    "timeline_breach": "Notify account manager"
                }
            ),
            prerequisites=["customer_data_complete", "service_configuration_ready"],
            roi_metrics={
                "onboarding_efficiency": "50% reduction in onboarding time",
                "customer_satisfaction": "30% improvement in satisfaction scores",
                "retention_rate": "20% improvement in customer retention"
            }
        )
        
        return {
            customer_onboarding.template_id: customer_onboarding
        }
    
    def _generate_workflows_from_templates(self):
        """Generate workflows from loaded templates"""
        
        for template_id, template in self.templates.items():
            workflow = template.workflow_definition
            self.workflows[workflow.workflow_id] = workflow
            
        logger.info(f"Generated {len(self.workflows)} workflows from templates")
    
    def _build_workflow_catalog(self):
        """Build comprehensive workflow catalog"""
        
        catalog_entries = []
        
        for workflow_id, workflow in self.workflows.items():
            # Find corresponding template for additional metadata
            template = next(
                (t for t in self.templates.values() if t.workflow_definition.workflow_id == workflow_id),
                None
            )
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(workflow)
            complexity_level = self._get_complexity_level(complexity_score)
            
            # Estimate duration from steps
            estimated_duration = sum(
                step.estimated_duration_minutes for step in workflow.steps
            )
            
            entry = WorkflowCatalogEntry(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                description=workflow.description,
                category=workflow.business_domain.value,
                business_domain=workflow.business_domain,
                complexity=complexity_level,
                estimated_duration_minutes=estimated_duration,
                steps_count=len(workflow.steps),
                success_rate=0.85,  # Default, would be updated with real data
                avg_completion_time_minutes=int(estimated_duration * 1.2),  # Add 20% buffer
                usage_count=0,
                tags=self._generate_workflow_tags(workflow, template),
                prerequisites=template.prerequisites if template else [],
                roi_metrics=template.roi_metrics if template else {}
            )
            
            catalog_entries.append(entry)
        
        self.catalog = catalog_entries
        logger.info(f"Built catalog with {len(catalog_entries)} workflow entries")
    
    def _calculate_complexity_score(self, workflow: BusinessWorkflow) -> float:
        """Calculate workflow complexity score"""
        
        base_score = len(workflow.steps) * 0.1
        
        # Add complexity for dependencies
        dependency_score = sum(len(step.dependencies) for step in workflow.steps) * 0.05
        
        # Add complexity for parallel execution
        parallel_score = sum(0.1 for step in workflow.steps if step.parallel_execution)
        
        # Add complexity for approval requirements
        approval_score = sum(0.1 for step in workflow.steps if step.approval_required)
        
        # Add complexity for tools required
        tools_score = sum(len(step.tools_required) * 0.02 for step in workflow.steps)
        
        total_score = base_score + dependency_score + parallel_score + approval_score + tools_score
        return min(1.0, total_score)
    
    def _get_complexity_level(self, score: float) -> str:
        """Convert complexity score to level"""
        if score < 0.3:
            return "low"
        elif score < 0.6:
            return "medium"
        else:
            return "high"
    
    def _generate_workflow_tags(
        self, workflow: BusinessWorkflow, template: Optional[WorkflowTemplate]
    ) -> List[str]:
        """Generate tags for workflow"""
        
        tags = [workflow.business_domain.value, workflow.priority.value]
        
        # Add step type tags
        step_types = {step.step_type.value for step in workflow.steps}
        tags.extend(step_types)
        
        # Add agent tags
        agent_types = set()
        for step in workflow.steps:
            if "strategic" in step.agent_name:
                agent_types.add("strategic")
            if "financial" in step.agent_name or "cfo" in step.agent_name:
                agent_types.add("financial")
            if "security" in step.agent_name:
                agent_types.add("security")
        tags.extend(agent_types)
        
        # Add template use cases if available
        if template:
            tags.extend([use_case.replace(" ", "_").lower() for use_case in template.use_cases[:3]])
        
        return list(set(tags))  # Remove duplicates
    
    def _initialize_usage_stats(self):
        """Initialize usage statistics tracking"""
        
        for workflow_id in self.workflows.keys():
            self.usage_stats[workflow_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_duration_minutes": 0.0,
                "last_executed": None,
                "success_rate": 0.0,
                "user_ratings": []
            }


# Global registry instance
_workflow_registry = ComprehensiveWorkflowRegistry()


# Public API functions
async def load_predefined_workflows() -> Dict[str, BusinessWorkflow]:
    """Load pre-defined business workflows"""
    return _workflow_registry.workflows


async def get_workflow(workflow_id: str) -> Optional[BusinessWorkflow]:
    """Get workflow by ID"""
    return _workflow_registry.workflows.get(workflow_id)


async def search_workflows(
    query: str = "",
    domain: Optional[str] = None,
    complexity: Optional[str] = None,
    max_duration_minutes: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Search workflows with filters"""
    
    results = _workflow_registry.catalog
    
    # Text search in name and description
    if query:
        query_lower = query.lower()
        results = [
            entry for entry in results
            if query_lower in entry.name.lower() 
            or query_lower in entry.description.lower()
            or any(query_lower in tag for tag in entry.tags)
        ]
    
    # Domain filter
    if domain:
        results = [entry for entry in results if entry.business_domain.value == domain.lower()]
    
    # Complexity filter
    if complexity:
        results = [entry for entry in results if entry.complexity == complexity]
    
    # Duration filter
    if max_duration_minutes:
        results = [
            entry for entry in results 
            if entry.estimated_duration_minutes <= max_duration_minutes
        ]
    
    # Sort by usage count and success rate
    results.sort(key=lambda x: (x.success_rate, x.usage_count), reverse=True)
    
    return [asdict(result) for result in results]


async def get_workflow_catalog() -> List[Dict[str, Any]]:
    """Get comprehensive workflow catalog"""
    return [asdict(entry) for entry in _workflow_registry.catalog]


# Legacy compatibility function
def get_workflow_catalog_legacy() -> List[Dict[str, str]]:
    """Legacy catalog function for backward compatibility"""
    catalog = [asdict(entry) for entry in _workflow_registry.catalog]
    
    # Convert to legacy format
    legacy_catalog = []
    for entry in catalog:
        legacy_catalog.append({
            "workflow_id": entry["workflow_id"],
            "name": entry["name"],
            "description": entry["description"],
            "category": entry["category"],
            "complexity": entry["complexity"],
            "estimated_duration": str(entry["estimated_duration_minutes"])
        })
    
    return legacy_catalog