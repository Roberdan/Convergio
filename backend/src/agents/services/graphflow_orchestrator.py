"""
GraphFlow Orchestrator for Convergio Business Processes
Advanced workflow patterns using AutoGen 0.7.1 GraphFlow capabilities
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import structlog
from uuid import uuid4

from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.core.config import settings
from src.agents.services.agent_loader import agent_loader
from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
from src.agents.security.ai_security_guardian import AISecurityGuardian
from src.core.redis import get_redis_client

logger = structlog.get_logger()

@dataclass
class WorkflowStep:
    """Represents a single step in a business workflow"""
    step_id: str
    agent_name: str
    step_type: str  # 'analysis', 'decision', 'action', 'validation'
    description: str
    inputs: List[str]
    outputs: List[str]
    conditions: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300

@dataclass
class BusinessWorkflow:
    """Defines a complete business workflow"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    entry_points: List[str]  # Starting step IDs
    exit_conditions: Dict[str, str]  # Step ID -> exit condition
    metadata: Dict[str, Any]

@dataclass
class WorkflowExecution:
    """Tracks execution of a workflow"""
    execution_id: str
    workflow_id: str
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    current_step: Optional[str]
    step_results: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]
    user_id: str

class GraphFlowOrchestrator:
    """Advanced workflow orchestrator using AutoGen GraphFlow"""
    
    def __init__(self):
        self.workflows: Dict[str, BusinessWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.memory_system = AutoGenMemorySystem()
        self.security_guardian = AISecurityGuardian()
        self.redis_client = None
        
    async def initialize(self):
        """Initialize the GraphFlow orchestrator"""
        logger.info("🚀 Initializing GraphFlow Orchestrator")
        
        # Initialize Redis connection
        self.redis_client = get_redis_client()
        
        # Load pre-defined business workflows
        await self._load_predefined_workflows()
        
        logger.info(f"✅ GraphFlow Orchestrator initialized with {len(self.workflows)} workflows")

    async def _load_predefined_workflows(self):
        """Load predefined business workflow templates"""
        
        # 1. Strategic Analysis Workflow
        strategic_workflow = BusinessWorkflow(
            workflow_id="strategic-analysis-001",
            name="Strategic Business Analysis",
            description="Comprehensive strategic analysis workflow for business decisions",
            steps=[
                WorkflowStep(
                    step_id="initial-analysis",
                    agent_name="ali_chief_of_staff",
                    step_type="analysis",
                    description="Initial strategic assessment and problem definition",
                    inputs=["user_request", "context"],
                    outputs=["strategic_assessment", "key_stakeholders"]
                ),
                WorkflowStep(
                    step_id="financial-analysis",
                    agent_name="amy_cfo",
                    step_type="analysis", 
                    description="Financial impact analysis and budget considerations",
                    inputs=["strategic_assessment"],
                    outputs=["financial_impact", "budget_requirements"]
                ),
                WorkflowStep(
                    step_id="technical-feasibility",
                    agent_name="baccio_tech_architect",
                    step_type="analysis",
                    description="Technical feasibility and architecture assessment",
                    inputs=["strategic_assessment"],
                    outputs=["technical_feasibility", "architecture_recommendations"]
                ),
                WorkflowStep(
                    step_id="risk-assessment",
                    agent_name="luca_security_expert",
                    step_type="validation",
                    description="Risk analysis and mitigation strategies",
                    inputs=["financial_impact", "technical_feasibility"],
                    outputs=["risk_analysis", "mitigation_strategies"]
                ),
                WorkflowStep(
                    step_id="final-recommendation",
                    agent_name="ali_chief_of_staff",
                    step_type="decision",
                    description="Synthesize all analyses into actionable recommendations",
                    inputs=["financial_impact", "technical_feasibility", "risk_analysis"],
                    outputs=["final_recommendations", "implementation_plan"]
                )
            ],
            entry_points=["initial-analysis"],
            exit_conditions={"final-recommendation": "recommendations_complete"},
            metadata={"category": "strategic", "complexity": "high", "estimated_duration": 1800}
        )
        
        # 2. Customer Onboarding Workflow
        onboarding_workflow = BusinessWorkflow(
            workflow_id="customer-onboarding-001",
            name="Customer Onboarding Process",
            description="Automated customer onboarding with multi-agent coordination",
            steps=[
                WorkflowStep(
                    step_id="customer-intake",
                    agent_name="andrea_customer_success_manager",
                    step_type="analysis",
                    description="Collect and analyze customer requirements",
                    inputs=["customer_data", "requirements"],
                    outputs=["customer_profile", "service_requirements"]
                ),
                WorkflowStep(
                    step_id="technical-setup",
                    agent_name="marco_devops_engineer",
                    step_type="action",
                    description="Configure technical infrastructure for customer",
                    inputs=["customer_profile", "service_requirements"],
                    outputs=["infrastructure_config", "access_credentials"]
                ),
                WorkflowStep(
                    step_id="security-validation",
                    agent_name="luca_security_expert",
                    step_type="validation",
                    description="Validate security setup and compliance",
                    inputs=["infrastructure_config"],
                    outputs=["security_clearance", "compliance_status"]
                ),
                WorkflowStep(
                    step_id="onboarding-complete",
                    agent_name="andrea_customer_success_manager",
                    step_type="action",
                    description="Finalize onboarding and customer handoff",
                    inputs=["security_clearance", "access_credentials"],
                    outputs=["onboarding_package", "next_steps"]
                )
            ],
            entry_points=["customer-intake"],
            exit_conditions={"onboarding-complete": "customer_activated"},
            metadata={"category": "operations", "complexity": "medium", "estimated_duration": 900}
        )
        
        # 3. Incident Response Workflow
        incident_workflow = BusinessWorkflow(
            workflow_id="incident-response-001",
            name="Security Incident Response",
            description="Automated incident response and resolution workflow",
            steps=[
                WorkflowStep(
                    step_id="incident-triage",
                    agent_name="luca_security_expert",
                    step_type="analysis",
                    description="Assess incident severity and impact",
                    inputs=["incident_report", "system_status"],
                    outputs=["severity_level", "impact_assessment"]
                ),
                WorkflowStep(
                    step_id="technical-investigation", 
                    agent_name="baccio_tech_architect",
                    step_type="analysis",
                    description="Technical root cause analysis",
                    inputs=["severity_level", "impact_assessment"],
                    outputs=["root_cause", "technical_details"]
                ),
                WorkflowStep(
                    step_id="communication-plan",
                    agent_name="ali_chief_of_staff",
                    step_type="action",
                    description="Coordinate stakeholder communication",
                    inputs=["severity_level", "impact_assessment"],
                    outputs=["communication_plan", "stakeholder_updates"]
                ),
                WorkflowStep(
                    step_id="resolution-implementation",
                    agent_name="marco_devops_engineer",
                    step_type="action",
                    description="Implement technical resolution",
                    inputs=["root_cause", "technical_details"],
                    outputs=["resolution_steps", "system_recovery"]
                ),
                WorkflowStep(
                    step_id="post-incident-review",
                    agent_name="ali_chief_of_staff",
                    step_type="validation",
                    description="Post-incident analysis and process improvement",
                    inputs=["resolution_steps", "communication_plan"],
                    outputs=["incident_report", "process_improvements"]
                )
            ],
            entry_points=["incident-triage"],
            exit_conditions={"post-incident-review": "incident_closed"},
            metadata={"category": "security", "complexity": "high", "estimated_duration": 3600}
        )
        
        # Store workflows
        self.workflows[strategic_workflow.workflow_id] = strategic_workflow
        self.workflows[onboarding_workflow.workflow_id] = onboarding_workflow
        self.workflows[incident_workflow.workflow_id] = incident_workflow
        
        logger.info(f"📋 Loaded {len(self.workflows)} predefined workflows")

    async def create_execution_graph(self, workflow: BusinessWorkflow) -> DiGraphBuilder:
        """Create AutoGen GraphFlow execution graph from workflow definition"""
        
        builder = DiGraphBuilder()
        
        # Create agents for each step
        step_agents = {}
        for step in workflow.steps:
            agent_config = await agent_loader.get_agent_config(step.agent_name)
            if not agent_config:
                logger.warning(f"⚠️ Agent {step.agent_name} not found, using default")
                agent_config = {
                    "name": step.agent_name,
                    "description": f"Agent for {step.step_type}",
                    "model": "gpt-4"
                }
            
            # Create AutoGen agent
            client = OpenAIChatCompletionClient(
                model=agent_config.get("model", "gpt-4"),
                api_key=settings.OPENAI_API_KEY
            )
            
            agent = AssistantAgent(
                name=f"{step.step_id}_agent",
                model_client=client,
                system_message=f"""You are {step.agent_name} working on: {step.description}
                
Your role: {step.step_type}
Expected inputs: {', '.join(step.inputs)}
Expected outputs: {', '.join(step.outputs)}

Provide structured, actionable responses that clearly address the required outputs.
"""
            )
            
            step_agents[step.step_id] = agent
            builder.add_node(agent)
        
        # Add edges based on workflow dependencies
        for step in workflow.steps:
            current_agent = step_agents[step.step_id]
            
            # Find dependent steps (steps that use this step's outputs)
            for dependent_step in workflow.steps:
                if any(output in dependent_step.inputs for output in step.outputs):
                    dependent_agent = step_agents[dependent_step.step_id]
                    
                    # Add edge with optional condition
                    if step.conditions:
                        # Create condition function
                        condition_func = self._create_condition_function(step.conditions)
                        builder.add_edge(current_agent, dependent_agent, condition=condition_func)
                    else:
                        builder.add_edge(current_agent, dependent_agent)
        
        return builder
    
    def _create_condition_function(self, conditions: Dict[str, Any]) -> Callable:
        """Create a condition function for GraphFlow edges"""
        
        def condition_check(messages) -> bool:
            if not messages:
                return False
                
            last_message = messages[-1]
            if not hasattr(last_message, 'content'):
                return False
                
            content = last_message.content.lower()
            
            # Check various condition types
            for condition_type, condition_value in conditions.items():
                if condition_type == "contains_keyword":
                    if condition_value.lower() in content:
                        return True
                elif condition_type == "min_length":
                    if len(content) >= condition_value:
                        return True
                elif condition_type == "status_complete":
                    if any(keyword in content for keyword in ["complete", "done", "finished", "ready"]):
                        return True
                        
            return False
        
        return condition_check

    async def execute_workflow(
        self,
        workflow_id: str,
        user_request: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Execute a business workflow asynchronously"""
        
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        workflow = self.workflows[workflow_id]
        execution_id = str(uuid4())
        
        # Create workflow execution tracking
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status="pending",
            current_step=None,
            step_results={},
            start_time=datetime.utcnow(),
            end_time=None,
            error_message=None,
            user_id=user_id
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Update status to running
            execution.status = "running"
            await self._save_execution_state(execution)
            
            logger.info(f"🚀 Starting workflow execution", 
                       workflow_id=workflow_id, execution_id=execution_id)
            
            # Create execution graph
            graph_builder = await self.create_execution_graph(workflow)
            graph = graph_builder.build()
            
            # Create GraphFlow team
            graphflow_team = GraphFlow(graph=graph)
            
            # Prepare initial message with context
            initial_context = {
                "user_request": user_request,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "context": context or {}
            }
            
            initial_message = f"""
WORKFLOW EXECUTION REQUEST

User Request: {user_request}

Context: {json.dumps(initial_context, indent=2)}

Please process this request according to your role in the {workflow.name} workflow.
Provide structured outputs as specified in your step definition.
            """
            
            # Execute workflow
            result = await graphflow_team.run(
                task=TextMessage(content=initial_message, source="user")
            )
            
            # Process results
            execution.step_results = await self._extract_workflow_results(result)
            execution.status = "completed"
            execution.end_time = datetime.utcnow()
            
            logger.info(f"✅ Workflow execution completed", 
                       workflow_id=workflow_id, execution_id=execution_id)
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed", 
                        workflow_id=workflow_id, execution_id=execution_id, 
                        error=str(e))
            execution.status = "failed"
            execution.error_message = str(e)
            execution.end_time = datetime.utcnow()
            
        finally:
            await self._save_execution_state(execution)
            
        return execution_id

    async def _extract_workflow_results(self, flow_result) -> Dict[str, Any]:
        """Extract structured results from GraphFlow execution"""
        
        results = {}
        
        try:
            if hasattr(flow_result, 'messages'):
                for message in flow_result.messages:
                    if hasattr(message, 'source') and hasattr(message, 'content'):
                        agent_name = message.source
                        content = message.content
                        
                        # Try to extract structured data
                        try:
                            # Look for JSON-like structures in the content
                            import re
                            json_matches = re.findall(r'\{[^{}]*\}', content)
                            for json_str in json_matches:
                                try:
                                    structured_data = json.loads(json_str)
                                    results[f"{agent_name}_structured"] = structured_data
                                except json.JSONDecodeError:
                                    pass
                        except:
                            pass
                        
                        # Store raw content as well
                        results[agent_name] = content
                        
        except Exception as e:
            logger.warning(f"⚠️ Could not extract structured results: {e}")
            results["raw_result"] = str(flow_result)
            
        return results
        
    async def _save_execution_state(self, execution: WorkflowExecution):
        """Save execution state to Redis for persistence"""
        
        try:
            if self.redis_client:
                key = f"workflow_execution:{execution.execution_id}"
                data = asdict(execution)
                # Convert datetime objects to ISO strings
                if data.get('start_time'):
                    data['start_time'] = data['start_time'].isoformat()
                if data.get('end_time'):
                    data['end_time'] = data['end_time'].isoformat()
                    
                await self.redis_client.setex(
                    key,
                    86400,  # 24 hours TTL
                    json.dumps(data, default=str)
                )
        except Exception as e:
            logger.warning(f"⚠️ Could not save execution state: {e}")

    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get current status of workflow execution"""
        
        if execution_id in self.executions:
            return self.executions[execution_id]
            
        # Try to load from Redis
        try:
            if self.redis_client:
                key = f"workflow_execution:{execution_id}"
                data = await self.redis_client.get(key)
                if data:
                    execution_data = json.loads(data)
                    # Convert ISO strings back to datetime
                    if execution_data.get('start_time'):
                        execution_data['start_time'] = datetime.fromisoformat(execution_data['start_time'])
                    if execution_data.get('end_time'):
                        execution_data['end_time'] = datetime.fromisoformat(execution_data['end_time'])
                        
                    execution = WorkflowExecution(**execution_data)
                    self.executions[execution_id] = execution
                    return execution
        except Exception as e:
            logger.warning(f"⚠️ Could not load execution from Redis: {e}")
            
        return None

    async def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows with metadata"""
        
        return [
            {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "category": workflow.metadata.get("category", "general"),
                "complexity": workflow.metadata.get("complexity", "medium"),
                "estimated_duration": workflow.metadata.get("estimated_duration", 1800),
                "steps_count": len(workflow.steps)
            }
            for workflow in self.workflows.values()
        ]

    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        
        execution = await self.get_workflow_status(execution_id)
        if execution and execution.status == "running":
            execution.status = "cancelled"
            execution.end_time = datetime.utcnow()
            await self._save_execution_state(execution)
            logger.info(f"🛑 Workflow execution cancelled", execution_id=execution_id)
            return True
        return False

# Global GraphFlow orchestrator instance - lazy loaded
graphflow_orchestrator = None

def get_graphflow_orchestrator() -> GraphFlowOrchestrator:
    """Get or create the global GraphFlow orchestrator instance"""
    global graphflow_orchestrator
    if graphflow_orchestrator is None:
        graphflow_orchestrator = GraphFlowOrchestrator()
    return graphflow_orchestrator