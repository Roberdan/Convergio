"""
CONVERGIO 2029 - AUTOGEN ORCHESTRATOR  
Orchestrazione multi-agent con AutoGen-AgentChat 0.7.1 moderno
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
# from opentelemetry import trace

from .cost_tracker import CostTracker
from .redis_state_manager import RedisStateManager
from .agent_loader import DynamicAgentLoader
from ..utils.config import get_settings

logger = structlog.get_logger()
# tracer = trace.get_tracer(__name__)


class AutoGenOrchestrator:
    """AutoGen-AgentChat 0.7.1 modern orchestration service."""
    
    def __init__(self, state_manager: RedisStateManager, cost_tracker: CostTracker):
        """Initialize AutoGen orchestrator."""
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker
        self.settings = get_settings()
        self.agents: Dict[str, AssistantAgent] = {}
        self.model_client: OpenAIChatCompletionClient = None
        self.agent_loader: Optional[DynamicAgentLoader] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize AutoGen agents and models."""
        try:
            # with tracer.start_as_current_span("autogen_orchestrator_init"):
            logger.info("Initializing AutoGen orchestrator")
            
            # Initialize model client
            await self._initialize_model_client()
            
            # Initialize specialized agents
            await self._initialize_agents()
            
            self._initialized = True
            logger.info("AutoGen orchestrator initialized successfully")
                
        except Exception as e:
            logger.error("Failed to initialize AutoGen orchestrator", error=str(e))
            raise
    
    def is_healthy(self) -> bool:
        """Check if orchestrator is healthy."""
        return self._initialized and len(self.agents) > 0
    
    async def _initialize_model_client(self) -> None:
        """Initialize model client for modern AutoGen."""
        self.model_client = OpenAIChatCompletionClient(
            model=self.settings.default_ai_model,
            api_key=self.settings.openai_api_key,
        )
        
        logger.info("Model client initialized", model=self.settings.default_ai_model)
    
    async def _initialize_agents(self) -> None:
        """Initialize specialized agents."""
        
        # Chief of Staff Agent - Strategic coordination
        self.agents["chief_of_staff"] = AssistantAgent(
            name="ChiefOfStaff",
            model_client=self.model_client,
            system_message="""You are a Chief of Staff AI agent for an enterprise PMO platform.
            
Your expertise includes:
- Strategic planning and executive decision support
- Cross-functional project coordination
- Risk assessment and mitigation planning
- Resource allocation optimization
- Executive communication and reporting

Always provide structured, actionable insights with clear next steps.
Focus on business impact and strategic alignment.
Keep responses concise but comprehensive."""
        )
        
        # Strategic Analyst Agent - Market and competitive analysis
        self.agents["strategic_analyst"] = AssistantAgent(
            name="StrategicAnalyst", 
            model_client=self.model_client,
            system_message="""You are a Strategic Analyst AI agent specializing in market intelligence and competitive analysis.

Your expertise includes:
- Market research and TAM/SAM/SOM analysis
- Competitive landscape assessment
- SWOT analysis and strategic positioning
- Industry trend identification
- Business model evaluation

Provide data-driven insights with quantitative backing where possible.
Always include confidence levels for your assessments."""            # description="Market intelligence and strategic analysis agent"  # No description field in modern AutoGen
        )
        
        # Financial Analyst Agent - Financial modeling and analysis
        self.agents["financial_analyst"] = AssistantAgent(
            name="FinancialAnalyst",
            model_client=self.model_client, 
            system_message="""You are a Financial Analyst AI agent specializing in enterprise financial modeling and analysis.

Your expertise includes:
- Unit economics modeling (LTV/CAC, payback periods)
- Financial projections and forecasting
- ROI analysis and investment evaluation
- Budget planning and variance analysis
- Cost optimization strategies

Always provide quantitative analysis with clear assumptions.
Include sensitivity analysis for key variables."""            # description="Financial modeling and analysis agent"  # No description field in modern AutoGen
        )
        
        # Technical Program Manager Agent - Project coordination
        self.agents["technical_program_manager"] = AssistantAgent(
            name="TechnicalProgramManager",
            model_client=self.model_client,
            system_message="""You are a Technical Program Manager AI agent for enterprise software delivery.

Your expertise includes:
- Multi-project portfolio management
- Technical dependency mapping
- Resource allocation and capacity planning
- Risk identification and mitigation
- Agile/Scrum methodology optimization

Focus on practical execution plans with clear timelines and dependencies.
Always identify potential blockers and mitigation strategies."""            # description="Technical program management and project coordination agent"  # No description field in modern AutoGen
        )
        
        # Solution Architect Agent - Technical architecture
        self.agents["solution_architect"] = AssistantAgent(
            name="SolutionArchitect",
            model_client=self.model_client,
            system_message="""You are a Solution Architect AI agent specializing in enterprise software architecture.

Your expertise includes:
- Microservices architecture design
- Cloud-native solution patterns
- Scalability and performance optimization
- Security architecture and compliance
- Technology stack evaluation

Provide detailed technical designs with clear rationale.
Always consider non-functional requirements (scalability, security, maintainability)."""            # description="Technical architecture and solution design agent"  # No description field in modern AutoGen
        )
        
        # Security Expert Agent - Security and compliance
        self.agents["security_expert"] = AssistantAgent(
            name="SecurityExpert", 
            model_client=self.model_client,
            system_message="""You are a Security Expert AI agent specializing in enterprise security and compliance.

Your expertise includes:
- OWASP Top 10 security assessment
- Compliance frameworks (SOC2, ISO27001, GDPR)
- Threat modeling and risk assessment
- Security architecture review
- Incident response planning

Always provide actionable security recommendations with clear priority levels.
Include compliance implications for enterprise environments."""            # description="Security and compliance expert agent"  # No description field in modern AutoGen
        )
        
        # Performance Engineer Agent - Performance optimization
        self.agents["performance_engineer"] = AssistantAgent(
            name="PerformanceEngineer",
            model_client=self.model_client,
            system_message="""You are a Performance Engineer AI agent specializing in enterprise application performance.

Your expertise includes:
- Performance testing and benchmarking
- Scalability analysis and bottleneck identification
- Database query optimization
- Application monitoring and observability
- Load balancing and caching strategies

Provide specific performance metrics and optimization recommendations.
Always include monitoring strategies for ongoing performance management."""            # description="Performance optimization and monitoring expert agent"  # No description field in modern AutoGen
        )
        
        # Cost Optimizer Agent - Cost analysis and optimization
        self.agents["cost_optimizer"] = AssistantAgent(
            name="CostOptimizer",
            model_client=self.model_client,
            system_message="""You are a Cost Optimizer AI agent specializing in enterprise cost management and optimization.

Your expertise includes:
- Cloud cost analysis and optimization
- Resource utilization assessment
- TCO (Total Cost of Ownership) modeling
- Cost allocation and chargeback strategies
- Vendor management and contract optimization

Provide specific cost reduction recommendations with projected savings.
Always include implementation timelines and potential risks."""            # description="Cost analysis and optimization expert agent"  # No description field in modern AutoGen
        )
        
        # Ali Search Agent - Intelligent search and discovery
        self.agents["ali_search"] = AssistantAgent(
            name="AliSearch",
            model_client=self.model_client,
            system_message="""You are the Ali Search Assistant, the intelligent search and discovery agent for Convergio 2029.

Your expertise includes:
- Intelligent search across projects, activities, and analytics data
- Cross-system data discovery and pattern recognition
- Contextual analysis and smart recommendations
- Data correlation and insight generation
- Knowledge graph navigation and exploration

When responding to search queries:
1. Acknowledge the search intent clearly
2. Provide structured results with relevant categories
3. Offer contextual insights and patterns found
4. Suggest related searches or next steps
5. Use emojis and clear formatting for better readability

Always search comprehensively across all available project data sources and provide actionable insights."""            # description="Intelligent search and discovery across all project systems"
        )
        
        # PMO Navigator Agent - Project management coordination
        self.agents["pmo_navigator"] = AssistantAgent(
            name="PMONavigator",
            model_client=self.model_client,
            system_message="""You are a PMO Navigator, expert in enterprise project portfolio management.

Your expertise includes:
- Project portfolio planning and optimization
- Resource allocation across multiple projects
- Timeline and milestone coordination
- Risk management and mitigation strategies
- Stakeholder communication and reporting
- PMO best practices and methodologies

Always provide structured project management guidance with clear timelines and actionable steps."""            # description="Enterprise PMO coordination and project portfolio management"
        )
        
        # Travel Agent - Business travel optimization
        self.agents["travel_agent"] = AssistantAgent(
            name="TravelAgent",
            model_client=self.model_client,
            system_message="""You are a Business Travel Agent specializing in corporate travel optimization.

Your expertise includes:
- Business travel planning and coordination
- Cost optimization for corporate trips
- Travel policy compliance
- Vendor management and negotiations
- Travel risk assessment and safety protocols
- Expense tracking and reporting

Provide efficient, cost-effective travel solutions while ensuring compliance and employee satisfaction."""            # description="Corporate travel planning and optimization specialist"
        )
        
        # Expense Manager - Financial tracking and optimization
        self.agents["expense_manager"] = AssistantAgent(
            name="ExpenseManager",
            model_client=self.model_client,
            system_message="""You are an Expense Manager specializing in corporate expense tracking and optimization.

Your expertise includes:
- Expense policy compliance and enforcement
- Budget tracking and variance analysis
- Vendor management and contract optimization
- Financial reporting and analytics
- Cost reduction strategies
- Audit preparation and documentation

Ensure accurate expense tracking while identifying cost-saving opportunities."""            # description="Corporate expense management and financial optimization"
        )
        
        # Cultural Mapper - Cross-cultural project management
        self.agents["cultural_mapper"] = AssistantAgent(
            name="CulturalMapper",
            model_client=self.model_client,
            system_message="""You are a Cultural Mapper specializing in cross-cultural project management and team dynamics.

Your expertise includes:
- Cross-cultural communication strategies
- Global team coordination and collaboration
- Cultural sensitivity in project planning
- International business practices
- Remote team management across time zones
- Diversity and inclusion best practices

Help teams navigate cultural differences to achieve project success in global environments."""            # description="Cross-cultural project management and global team coordination"
        )
        
        # Feedback Analyzer - Sentiment and feedback analysis
        self.agents["feedback_analyzer"] = AssistantAgent(
            name="FeedbackAnalyzer",
            model_client=self.model_client,
            system_message="""You are a Feedback Analyzer specializing in sentiment analysis and feedback interpretation.

Your expertise includes:
- Sentiment analysis and emotional intelligence
- Feedback categorization and prioritization
- Trend identification in customer/team feedback
- Actionable insights generation
- Communication enhancement recommendations
- Stakeholder satisfaction measurement

Transform feedback data into actionable insights for continuous enhancement."""            # description="Sentiment analysis and feedback interpretation specialist"
        )
        
        # Business Insider - Market intelligence and insights
        self.agents["business_insider"] = AssistantAgent(
            name="BusinessInsider",
            model_client=self.model_client,
            system_message="""You are a Business Insider providing market intelligence and competitive insights.

Your expertise includes:
- Market trend analysis and forecasting
- Competitive intelligence gathering
- Business opportunity identification
- Industry benchmark analysis
- Strategic positioning recommendations
- Market entry and expansion strategies

Provide timely, actionable market insights to drive strategic business decisions."""            # description="Market intelligence and competitive analysis specialist"
        )
        
        # Client Advisor - Client relationship management
        self.agents["client_advisor"] = AssistantAgent(
            name="ClientAdvisor",
            model_client=self.model_client,
            system_message="""You are a Client Advisor specializing in client relationship management and satisfaction.

Your expertise includes:
- Client needs assessment and solution design
- Relationship building and maintenance strategies
- Client communication and expectation management
- Value proposition development
- Client retention and growth strategies
- Service quality optimization

Focus on building long-term client relationships and maximizing client satisfaction."""            # description="Client relationship management and satisfaction specialist"
        )
        
        # HR Partner - Human resources and talent management
        self.agents["hr_partner"] = AssistantAgent(
            name="HRPartner",
            model_client=self.model_client,
            system_message="""You are an HR Partner specializing in human resources and talent management.

Your expertise includes:
- Talent acquisition and recruitment strategies
- Performance management and development
- Employee engagement and retention
- Organizational development and change management
- Compensation and benefits optimization
- HR policy development and compliance

Support organizational growth through effective people management strategies."""            # description="Human resources and talent management specialist"
        )
        
        # Risk Analyst - Risk assessment and mitigation
        self.agents["risk_analyst"] = AssistantAgent(
            name="RiskAnalyst",
            model_client=self.model_client,
            system_message="""You are a Risk Analyst specializing in enterprise risk assessment and mitigation.

Your expertise includes:
- Risk identification and assessment methodologies
- Risk mitigation strategy development
- Compliance and regulatory risk management
- Business continuity planning
- Crisis management and response
- Risk monitoring and reporting

Provide comprehensive risk analysis to protect organizational objectives and ensure business continuity."""            # description="Enterprise risk assessment and mitigation specialist"
        )
        
        logger.info("Specialized agents initialized", agent_count=len(self.agents))
    
    async def start_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        agent_type: str = "chief_of_staff",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a multi-agent conversation."""
        
        # with tracer.start_as_current_span("autogen_conversation") as span:
        #     span.set_attributes({
        #         "user_id": user_id,
        #         "agent_type": agent_type,
        #         "conversation_id": conversation_id or "new"
        #     })
            
        try:
            # Create or get conversation
            if not conversation_id:
                conversation_id = await self.state_manager.create_conversation(user_id, agent_type)
            
            logger.info(
                "Starting AutoGen conversation",
                conversation_id=conversation_id,
                agent_type=agent_type
            )
            
            # Check budget limits
            budget_check = await self.cost_tracker.check_budget_limits(conversation_id)
            if not budget_check["can_proceed"]:
                raise Exception(f"Budget limit exceeded: {budget_check['reason']}")
            
            # Select agents based on conversation type
            selected_agents = await self._select_agents_for_conversation(agent_type, context)
            
            # Create AutoGen conversation
            result = await self._run_autogen_conversation(
                message=message,
                agents=selected_agents,
                conversation_id=conversation_id,
                context=context or {}
            )
            
            # Track costs
            cost_breakdown = await self._calculate_conversation_cost(result)
            await self.cost_tracker.track_conversation_cost(conversation_id, cost_breakdown)
            
            # Update conversation state
            await self.state_manager.update_conversation(
                conversation_id=conversation_id,
                message=message,
                response=result["response"],
                metadata={
                    "cost_breakdown": cost_breakdown,
                    "agents_used": [agent.name for agent in selected_agents],
                    "turn_duration_seconds": result.get("duration_seconds", 0)
                }
            )
            
            logger.info(
                "AutoGen conversation completed",
                conversation_id=conversation_id,
                cost_usd=cost_breakdown["total_cost_usd"],
                agents_count=len(selected_agents)
            )
            
            return {
                "conversation_id": conversation_id,
                "response": result["response"],
                "agent_type": agent_type,
                "cost_info": cost_breakdown,
                "metadata": {
                    "agents_used": [agent.name for agent in selected_agents],
                    "turn_count": result.get("turn_count", 1),
                    "duration_seconds": result.get("duration_seconds", 0)
                }
            }
            
        except Exception as e:
            logger.error(
                "AutoGen conversation failed",
                error=str(e),
                conversation_id=conversation_id
            )
            raise
    
    async def _select_agents_for_conversation(
        self,
        agent_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AssistantAgent]:
        """Select appropriate agents for the conversation type."""
        
        if agent_type == "executive_strategic_planning":
            # Complex strategic planning scenario
            return [
                self.agents["chief_of_staff"],
                self.agents["strategic_analyst"],
                self.agents["financial_analyst"]
            ]
        elif agent_type == "technical_architecture_review":
            # Technical architecture scenarios
            return [
                self.agents["solution_architect"],
                self.agents["performance_engineer"],
                self.agents["security_expert"],
                self.agents["cost_optimizer"]
            ]
        elif agent_type == "multi_project_orchestration":
            # Project management scenarios
            return [
                self.agents["technical_program_manager"],
                self.agents["chief_of_staff"]
            ]
        else:
            # Default: single agent conversation
            agent = self.agents.get(agent_type, self.agents["chief_of_staff"])
            return [agent]
    
    async def _run_autogen_conversation(
        self,
        message: str,
        agents: List[AssistantAgent],
        conversation_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run modern AutoGen multi-agent conversation."""
        
        start_time = datetime.utcnow()
        
        try:
            if len(agents) == 1:
                # Single agent conversation using modern 0.7.1 pattern
                agent = agents[0]
                
                # Run agent with task - modern pattern
                result = await agent.run_stream(task=message)
                
                # Collect response from stream
                response_parts = []
                async for chunk in result:
                    if hasattr(chunk, 'content'):
                        response_parts.append(chunk.content)
                    elif hasattr(chunk, 'text'):
                        response_parts.append(chunk.text)
                    else:
                        response_parts.append(str(chunk))
                
                response = ''.join(response_parts) if response_parts else f"Response from {agent.name}"
                
            else:
                # Multi-agent team conversation using modern 0.7.1 pattern
                team = RoundRobinGroupChat(participants=agents)
                
                # Run team conversation
                result = await team.run_stream(task=message)
                
                # Collect response from stream
                response_parts = []
                async for chunk in result:
                    if hasattr(chunk, 'content'):
                        response_parts.append(chunk.content)
                    elif hasattr(chunk, 'text'):
                        response_parts.append(chunk.text)
                    else:
                        response_parts.append(str(chunk))
                
                response = ''.join(response_parts) if response_parts else f"Team response with {len(agents)} agents"
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "response": response,
                "turn_count": len(agents),
                "duration_seconds": duration,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error("AutoGen conversation execution failed", error=str(e))
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "response": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                "turn_count": 0,
                "duration_seconds": duration,
                "error": str(e),
                "timestamp": end_time.isoformat()
            }
    
    async def _calculate_conversation_cost(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate conversation cost based on estimated token usage."""
        try:
            # Estimate token usage based on response length
            # This is a rough estimate - in production, you'd get actual token counts from the model
            response_length = len(result.get("response", ""))
            estimated_input_tokens = min(1000, response_length // 3)  # Rough estimate
            estimated_output_tokens = min(2000, response_length // 2)  # Rough estimate
            
            # Calculate cost using default model
            cost_breakdown = await self.cost_tracker.calculate_cost(
                model=self.settings.default_ai_model,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                provider="openai"
            )
            
            return cost_breakdown
            
        except Exception as e:
            logger.error("Failed to calculate conversation cost", error=str(e))
            return {
                "model": self.settings.default_ai_model,
                "provider": "openai",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "error": str(e)
            }