"""
CONVERGIO 2030 - ALI CHIEF OF STAFF SWARM ORCHESTRATOR
Master orchestrator implementing the complete 40+ agent ecosystem
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.messages import HandoffMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .cost_tracker import CostTracker
from .redis_state_manager import RedisStateManager
from .agent_loader import DynamicAgentLoader, AgentMetadata
from ..utils.config import get_settings
from ..tools.backend_api_client import query_talents_count, query_engagements_summary, query_dashboard_stats, query_skills_overview
from ..tools.vector_search_client import search_talents_by_skills, search_projects_by_requirements, search_knowledge_base, semantic_search, contextual_business_search

logger = structlog.get_logger()

@dataclass
class AgentSelectionResult:
    """Result of agent selection for task routing."""
    primary_agents: List[str]
    secondary_agents: List[str]
    confidence_score: float
    reasoning: str

@dataclass
class SwarmConversationResult:
    """Result of a swarm conversation."""
    response: str
    agents_used: List[str]
    turn_count: int
    duration_seconds: float
    routing_decisions: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Any]
    timestamp: str

class AliSwarmOrchestrator:
    """Ali Chief of Staff - Master orchestrator for the entire MyConvergio agent ecosystem."""
    
    def __init__(self, 
                 state_manager: RedisStateManager, 
                 cost_tracker: CostTracker,
                 agents_directory: str = None):
        """Initialize Ali Swarm Orchestrator."""
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker
        self.settings = get_settings()
        
        # Core components
        self.model_client: OpenAIChatCompletionClient = None
        self.agent_loader: DynamicAgentLoader = None
        self.agents: Dict[str, AssistantAgent] = {}
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        
        # Ali-specific orchestration
        self.ali_agent: AssistantAgent = None
        
        # Intelligence systems
        self.routing_intelligence: Dict[str, Any] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.agents_directory = agents_directory or "agents/src/agents"
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the complete Ali ecosystem."""
        try:
            logger.info("🚀 Initializing Ali Chief of Staff Swarm Orchestrator")
            
            # Initialize model client
            await self._initialize_model_client()
            
            # Load all agent definitions
            await self._initialize_agent_loader()
            
            # Create all AutoGen agents
            await self._create_all_agents()
            
            # Initialize Ali as the master orchestrator
            await self._initialize_ali_orchestrator()
            
            # Build routing intelligence
            await self._build_routing_intelligence()
            
            self._initialized = True
            logger.info(
                "✅ Ali Swarm Orchestrator initialized successfully",
                total_agents=len(self.agents),
                agent_tiers=len(set(a.tier for a in self.agent_metadata.values()))
            )
                
        except Exception as e:
            logger.error("❌ Failed to initialize Ali Swarm Orchestrator", error=str(e))
            raise
    
    def is_healthy(self) -> bool:
        """Check if the swarm orchestrator is healthy."""
        return (
            self._initialized 
            and self.ali_agent is not None
            and len(self.agents) >= 30  # Should have most agents loaded
            and self.model_client is not None
        )
    
    async def _initialize_model_client(self) -> None:
        """Initialize OpenAI model client."""
        self.model_client = OpenAIChatCompletionClient(
            model=self.settings.default_ai_model,
            api_key=self.settings.openai_api_key,
        )
        logger.info("🤖 Model client initialized", model=self.settings.default_ai_model)
    
    async def _initialize_agent_loader(self) -> None:
        """Initialize dynamic agent loader."""
        self.agent_loader = DynamicAgentLoader(self.agents_directory)
        self.agent_metadata = self.agent_loader.scan_and_load_agents()
        
        logger.info(
            "📚 Agent definitions loaded",
            total_agents=len(self.agent_metadata),
            agent_count=self.agent_loader.get_agent_count()
        )
    
    async def _create_all_agents(self) -> None:
        """Create all AutoGen agents from loaded definitions."""
        self.agents = self.agent_loader.create_autogen_agents(self.model_client)
        
        logger.info(
            "🎭 All AutoGen agents created",
            total_agents=len(self.agents),
            strategic_tier=len(self.agent_loader.get_agents_by_tier("Strategic Leadership")),
            tech_tier=len(self.agent_loader.get_agents_by_tier("Technology & Engineering"))
        )
    
    async def _initialize_ali_orchestrator(self) -> None:
        """Initialize Ali as the master orchestrator agent."""
        
        # Generate comprehensive knowledge base for Ali
        agent_knowledge = self.agent_loader.generate_ali_knowledge_base()
        
        # Build Ali's master system message
        ali_system_message = f"""You are **Ali**, the elite Chief of Staff for the MyConvergio ecosystem — the master orchestrator and single point of contact who coordinates all {len(self.agents)} specialist agents to deliver comprehensive, integrated strategic solutions.

## AGENT ECOSYSTEM KNOWLEDGE
{agent_knowledge}

## ORCHESTRATION PROTOCOL

### 1. REQUEST ANALYSIS
- Parse user request complexity and domain requirements
- Identify required expertise areas and agent combinations
- Determine if single-agent or multi-agent coordination is needed

### 2. INTELLIGENT AGENT ROUTING
- Select optimal agents based on expertise matching
- Use HandoffMessage for agent coordination
- Consider workload balancing and agent availability

### 3. QUALITY ORCHESTRATION
- Ensure consistent excellence across all agent interactions
- Validate that recommendations work together without conflicts
- Synthesize diverse perspectives into unified solutions

### 4. EXECUTIVE SYNTHESIS
- Present integrated solutions with clear implementation guidance
- Maintain single point of contact experience
- Provide executive-ready strategic recommendations

## ROUTING EXAMPLES
- Strategic planning → satya_board_of_directors, domik_mckinsey_strategic_decision_maker, antonio_strategy_expert
- Technical architecture → baccio_tech_architect, dan_engineering_gm, luca_security_expert
- Product development → sara_ux_ui_designer, jony_creative_director, sam_startupper
- Business operations → amy_cfo, fabio_sales_business_development, luke_program_manager

## COMMUNICATION STANDARDS
- Always start with strategic assessment of the request
- Explain your agent selection reasoning briefly
- Coordinate seamlessly between agents using HandoffMessage
- Synthesize all responses into coherent, actionable guidance
- Maintain executive-level professionalism throughout

Remember: You are the single point of strategic excellence. Every interaction should demonstrate the power of coordinated expertise delivered through seamless orchestration.
"""
        
        # Create Ali agent
        self.ali_agent = AssistantAgent(
            name="Ali",
            model_client=self.model_client,
            system_message=ali_system_message
        )
        
        # Note: UserProxyAgent in AutoGen 0.7.1 has different initialization
        # We'll handle user proxy functionality within Ali orchestration
        
        logger.info("👑 Ali Chief of Staff orchestrator initialized")
    
    async def _build_routing_intelligence(self) -> None:
        """Build intelligent routing system for optimal agent selection."""
        
        # Expertise mapping
        expertise_keywords = {}
        for key, metadata in self.agent_metadata.items():
            for keyword in metadata.expertise_keywords:
                if keyword not in expertise_keywords:
                    expertise_keywords[keyword] = []
                expertise_keywords[keyword].append(key)
        
        # Tier-based routing
        tier_mapping = {}
        for key, metadata in self.agent_metadata.items():
            tier = metadata.tier
            if tier not in tier_mapping:
                tier_mapping[tier] = []
            tier_mapping[tier].append(key)
        
        # Collaboration patterns
        collaboration_patterns = {
            "strategic_planning": ["satya_board_of_directors", "domik_mckinsey_strategic_decision_maker", "antonio_strategy_expert", "amy_cfo"],
            "product_development": ["sara_ux_ui_designer", "jony_creative_director", "baccio_tech_architect", "sam_startupper"],
            "technical_architecture": ["baccio_tech_architect", "dan_engineering_gm", "marco_devops_engineer", "luca_security_expert"],
            "business_operations": ["amy_cfo", "fabio_sales_business_development", "luke_program_manager", "andrea_customer_success_manager"],
            "organizational_transformation": ["giulia_hr_talent_acquisition", "coach_team_coach", "behice_cultural_coach", "dave_change_management_specialist"]
        }
        
        self.routing_intelligence = {
            "expertise_keywords": expertise_keywords,
            "tier_mapping": tier_mapping,
            "collaboration_patterns": collaboration_patterns,
            "total_agents": len(self.agents)
        }
        
        logger.info("🧠 Routing intelligence system built", patterns=len(collaboration_patterns))
    
    def _gather_system_context(self) -> str:
        """Gather current system data for Ali's context."""
        try:
            # Get all current system data
            talents_info = query_talents_count()
            engagements_info = query_engagements_summary()  
            dashboard_info = query_dashboard_stats()
            skills_info = query_skills_overview()
            
            context = f"""
=== CURRENT CONVERGIO SYSTEM DATA ===

TALENT DATABASE: {talents_info}
ENGAGEMENT STATUS: {engagements_info}
SKILLS INVENTORY: {skills_info}

COMPREHENSIVE DASHBOARD STATS: {dashboard_info}

=== SEMANTIC SEARCH CAPABILITIES ===
Ali now has access to advanced semantic search tools:
- search_talents_by_skills: Find talents with specific capabilities
- search_projects_by_requirements: Locate projects matching criteria  
- search_knowledge_base: Access organizational knowledge
- semantic_search: General semantic search across all content
- contextual_business_search: Business-focused strategic search

=== END SYSTEM DATA ===

Use this real-time data and semantic search capabilities to provide accurate, data-driven insights about our business operations.
"""
            return context
            
        except Exception as e:
            logger.warning("Failed to gather system context", error=str(e))
            return "\n=== SYSTEM DATA UNAVAILABLE ===\nWorking in offline mode without real-time system data.\n"
    
    def _enhance_context_with_semantic_search(self, message: str, base_context: str) -> str:
        """Enhance context with relevant semantic search results based on the user's message."""
        try:
            # Analyze message to determine what kind of semantic search would be helpful
            message_lower = message.lower()
            enhanced_context = base_context
            
            # If asking about talents, skills, or capabilities
            if any(term in message_lower for term in ['talent', 'skill', 'capability', 'expert', 'team', 'developer', 'engineer']):
                try:
                    search_result = search_talents_by_skills(message, 3)
                    enhanced_context += f"\n\n=== RELEVANT TALENTS (Semantic Search) ===\n{search_result}\n"
                except Exception as e:
                    logger.warning("Failed to search talents", error=str(e))
            
            # If asking about projects, work, or activities
            if any(term in message_lower for term in ['project', 'work', 'activity', 'deliver', 'timeline', 'roadmap']):
                try:
                    search_result = search_projects_by_requirements(message, 3)
                    enhanced_context += f"\n\n=== RELEVANT PROJECTS (Semantic Search) ===\n{search_result}\n"
                except Exception as e:
                    logger.warning("Failed to search projects", error=str(e))
            
            # If asking strategic business questions  
            if any(term in message_lower for term in ['strategy', 'business', 'growth', 'revenue', 'client', 'opportunity']):
                try:
                    search_result = contextual_business_search(message, 3)
                    enhanced_context += f"\n\n=== STRATEGIC BUSINESS CONTEXT (Semantic Search) ===\n{search_result}\n"
                except Exception as e:
                    logger.warning("Failed to search business context", error=str(e))
            
            # General knowledge search for complex questions
            if len(message.split()) > 10:  # Complex questions likely need knowledge context
                try:
                    search_result = search_knowledge_base(message, 2)
                    enhanced_context += f"\n\n=== RELEVANT KNOWLEDGE (Semantic Search) ===\n{search_result}\n"
                except Exception as e:
                    logger.warning("Failed to search knowledge base", error=str(e))
            
            return enhanced_context
            
        except Exception as e:
            logger.warning("Failed to enhance context with semantic search", error=str(e))
            return base_context
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_turns: int = 5
    ) -> SwarmConversationResult:
        """Orchestrate a complete swarm conversation through Ali."""
        
        start_time = datetime.utcnow()
        routing_decisions = []
        
        try:
            # Create or get conversation
            if not conversation_id:
                conversation_id = await self.state_manager.create_conversation(user_id, "ali_swarm")
            else:
                # Validate existing conversation or create if not found
                existing_conv = await self.state_manager.get_conversation(conversation_id)
                if not existing_conv:
                    logger.info("Conversation not found, creating new one", conversation_id=conversation_id)
                    conversation_id = await self.state_manager.create_conversation(user_id, "ali_swarm")
            
            logger.info(
                "🎪 Starting Ali swarm orchestration",
                conversation_id=conversation_id,
                message_length=len(message)
            )
            
            # Check budget limits
            budget_check = await self.cost_tracker.check_budget_limits(conversation_id)
            if not budget_check["can_proceed"]:
                raise Exception(f"Budget limit exceeded: {budget_check['reason']}")
            
            # Intelligent agent selection
            selection_result = await self._intelligent_agent_selection(message, context)
            routing_decisions.append({
                "type": "agent_selection",
                "agents_selected": selection_result.primary_agents + selection_result.secondary_agents,
                "confidence": selection_result.confidence_score,
                "reasoning": selection_result.reasoning,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Gather system context
            system_context = self._gather_system_context()
            logger.info("System context gathered", context_length=len(system_context))
            
            # Enhance context with semantic search based on message content
            enhanced_system_context = self._enhance_context_with_semantic_search(message, system_context)
            logger.info("System context enhanced with semantic search", 
                       enhanced_length=len(enhanced_system_context),
                       enhancement_added=len(enhanced_system_context) - len(system_context))
            
            enhanced_context = context or {}
            enhanced_context["system_data"] = enhanced_system_context
            
            # Execute swarm conversation with system context
            conversation_result = await self._execute_swarm_conversation(
                message=message,
                selected_agents=selection_result.primary_agents,
                conversation_id=conversation_id,
                context=enhanced_context,
                max_turns=max_turns
            )
            
            # Calculate costs
            cost_breakdown = await self._calculate_swarm_cost(conversation_result, selection_result)
            await self.cost_tracker.track_conversation_cost(conversation_id, cost_breakdown)
            
            # Update conversation state
            await self.state_manager.update_conversation(
                conversation_id=conversation_id,
                message=message,
                response=conversation_result["response"],
                metadata={
                    "cost_breakdown": cost_breakdown,
                    "agents_used": conversation_result["agents_used"],
                    "routing_decisions": routing_decisions,
                    "swarm_orchestration": True
                }
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            result = SwarmConversationResult(
                response=conversation_result["response"],
                agents_used=conversation_result["agents_used"],
                turn_count=conversation_result["turn_count"],
                duration_seconds=duration,
                routing_decisions=routing_decisions,
                cost_breakdown=cost_breakdown,
                timestamp=end_time.isoformat()
            )
            
            logger.info(
                "✅ Ali swarm orchestration completed",
                conversation_id=conversation_id,
                agents_used=len(result.agents_used),
                duration_seconds=duration,
                cost_usd=cost_breakdown.get("total_cost_usd", 0)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "❌ Ali swarm orchestration failed",
                error=str(e),
                conversation_id=conversation_id
            )
            raise
    
    async def _intelligent_agent_selection(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentSelectionResult:
        """Intelligently select agents based on message analysis."""
        
        message_lower = message.lower()
        selected_agents = []
        confidence_score = 0.0
        reasoning_parts = []
        
        # Keyword-based matching
        keyword_matches = {}
        for keyword, agent_keys in self.routing_intelligence["expertise_keywords"].items():
            if keyword in message_lower:
                for agent_key in agent_keys:
                    if agent_key not in keyword_matches:
                        keyword_matches[agent_key] = 0
                    keyword_matches[agent_key] += 1
        
        # Pattern-based matching
        pattern_matches = []
        patterns = self.routing_intelligence["collaboration_patterns"]
        
        if any(term in message_lower for term in ["strategy", "strategic", "planning", "vision", "roadmap"]):
            pattern_matches.extend(patterns.get("strategic_planning", []))
            reasoning_parts.append("Strategic planning keywords detected")
        
        if any(term in message_lower for term in ["product", "development", "feature", "design", "user"]):
            pattern_matches.extend(patterns.get("product_development", []))
            reasoning_parts.append("Product development focus identified")
        
        if any(term in message_lower for term in ["technical", "architecture", "system", "infrastructure", "security"]):
            pattern_matches.extend(patterns.get("technical_architecture", []))
            reasoning_parts.append("Technical architecture requirements found")
        
        if any(term in message_lower for term in ["business", "operations", "sales", "revenue", "customer"]):
            pattern_matches.extend(patterns.get("business_operations", []))
            reasoning_parts.append("Business operations focus detected")
        
        if any(term in message_lower for term in ["team", "organization", "culture", "change", "transformation"]):
            pattern_matches.extend(patterns.get("organizational_transformation", []))
            reasoning_parts.append("Organizational transformation elements identified")
        
        # Combine and prioritize selections
        all_candidates = set(keyword_matches.keys()) | set(pattern_matches)
        
        # Score each candidate
        agent_scores = {}
        for agent_key in all_candidates:
            score = 0
            if agent_key in keyword_matches:
                score += keyword_matches[agent_key] * 2  # Keyword matches are strong
            if agent_key in pattern_matches:
                score += 1  # Pattern matches add to score
            agent_scores[agent_key] = score
        
        # Select top agents (limit to 4 for efficiency)
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agents = [agent[0] for agent in sorted_agents[:4]]
        
        # Always include Ali for orchestration
        if "ali_chief_of_staff" not in selected_agents:
            selected_agents.insert(0, "ali_chief_of_staff")
        
        # Calculate confidence
        if agent_scores:
            max_score = max(agent_scores.values())
            confidence_score = min(max_score / 5.0, 1.0)  # Normalize to 0-1
        else:
            # Fallback to strategic agents
            selected_agents = ["ali_chief_of_staff", "satya_board_of_directors", "domik_mckinsey_strategic_decision_maker"]
            confidence_score = 0.6
            reasoning_parts.append("Fallback to strategic leadership team")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "General strategic consultation"
        
        return AgentSelectionResult(
            primary_agents=selected_agents,
            secondary_agents=[],
            confidence_score=confidence_score,
            reasoning=reasoning
        )
    
    async def _execute_swarm_conversation(
        self,
        message: str,
        selected_agents: List[str],
        conversation_id: str,
        context: Dict[str, Any],
        max_turns: int
    ) -> Dict[str, Any]:
        """Execute the actual swarm conversation with selected agents."""
        
        try:
            # Filter to available agents
            available_agents = []
            for agent_key in selected_agents:
                if agent_key in self.agents:
                    available_agents.append(self.agents[agent_key])
                else:
                    logger.warning(f"Agent {agent_key} not found in loaded agents")
            
            if not available_agents:
                raise Exception("No valid agents available for conversation")
            
            # Prepare enhanced message with system context
            enhanced_message = message
            if "system_data" in context:
                enhanced_message = f"{context['system_data']}\n\nUSER REQUEST: {message}"
                logger.info("Enhanced message created", 
                           enhanced_length=len(enhanced_message),
                           has_system_data=True)
            else:
                logger.warning("No system data in context", context_keys=list(context.keys()))
            
            # Single agent conversation
            if len(available_agents) == 1:
                agent = available_agents[0]
                result = await agent.run_stream(task=enhanced_message)
                
                response_parts = []
                async for chunk in result:
                    if hasattr(chunk, 'content'):
                        response_parts.append(chunk.content)
                    elif hasattr(chunk, 'text'):
                        response_parts.append(chunk.text)
                    else:
                        response_parts.append(str(chunk))
                
                response = ''.join(response_parts) if response_parts else f"Strategic guidance from {agent.name}"
                
                return {
                    "response": response,
                    "agents_used": [agent.name],
                    "turn_count": 1
                }
            
            # Multi-agent swarm conversation
            else:
                # Use SelectorGroupChat for intelligent conversation flow (AutoGen 0.7.1 API)
                team = SelectorGroupChat(
                    participants=available_agents,
                    model_client=self.model_client,
                    allow_repeated_speaker=False,
                    max_turns=max_turns,
                    selector_prompt="""You are Ali, the Chief of Staff orchestrating a strategic consultation with multiple specialists. 

Available specialists: {participants}

Read the conversation history and select the next specialist who should respond based on:
1. Expertise relevance to the current topic
2. Natural conversation flow
3. Complementary perspectives needed

Only return the name of the specialist who should speak next.

{history}"""
                )
                
                # Use the correct AutoGen 0.7.1 API
                task_result = await team.run(task=enhanced_message)
                
                # Extract response from TaskResult
                response = ""
                if hasattr(task_result, 'messages') and task_result.messages:
                    # Get the last message content
                    last_message = task_result.messages[-1]
                    if hasattr(last_message, 'content'):
                        response = last_message.content
                    elif hasattr(last_message, 'text'):
                        response = last_message.text
                    else:
                        response = str(last_message)
                else:
                    response = f"Coordinated response from {len(available_agents)} specialists"
                
                return {
                    "response": response,
                    "agents_used": [agent.name for agent in available_agents],
                    "turn_count": len(task_result.messages) if hasattr(task_result, 'messages') else len(available_agents)
                }
                
        except Exception as e:
            logger.error("Swarm conversation execution failed", error=str(e))
            
            # Fallback response
            return {
                "response": f"I apologize, but I encountered an issue coordinating the specialist response. However, I can provide strategic guidance: {message}. Let me address your request directly and suggest the best path forward based on my strategic analysis.",
                "agents_used": ["Ali"],
                "turn_count": 1,
                "error": str(e)
            }
    
    async def _calculate_swarm_cost(
        self, 
        conversation_result: Dict[str, Any], 
        selection_result: AgentSelectionResult
    ) -> Dict[str, Any]:
        """Calculate cost for swarm conversation."""
        try:
            response_length = len(conversation_result.get("response", ""))
            agents_count = len(conversation_result.get("agents_used", []))
            
            # Estimate tokens (swarm conversations typically use more tokens)
            estimated_input_tokens = min(2000, response_length // 2) * agents_count
            estimated_output_tokens = min(3000, response_length) * agents_count
            
            cost_breakdown = await self.cost_tracker.calculate_cost(
                model=self.settings.default_ai_model,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                provider="openai"
            )
            
            # Add swarm-specific metadata
            cost_breakdown.update({
                "swarm_orchestration": True,
                "agents_count": agents_count,
                "routing_confidence": selection_result.confidence_score
            })
            
            return cost_breakdown
            
        except Exception as e:
            logger.error("Failed to calculate swarm conversation cost", error=str(e))
            return {
                "model": self.settings.default_ai_model,
                "provider": "openai",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "swarm_orchestration": True,
                "error": str(e)
            }
    
    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status."""
        return {
            "initialized": self._initialized,
            "total_agents": len(self.agents),
            "agent_tiers": len(set(a.tier for a in self.agent_metadata.values())),
            "routing_patterns": len(self.routing_intelligence.get("collaboration_patterns", {})),
            "ali_ready": self.ali_agent is not None,
            "model": self.settings.default_ai_model,
            "health_score": 1.0 if self.is_healthy() else 0.0
        }
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload all agents (useful for development)."""
        logger.info("🔄 Reloading Ali ecosystem agents")
        
        # Reload agent definitions
        self.agent_metadata = self.agent_loader.reload_agents()
        
        # Recreate AutoGen agents
        self.agents = self.agent_loader.create_autogen_agents(self.model_client)
        
        # Rebuild routing intelligence
        await self._build_routing_intelligence()
        
        # Reinitialize Ali with updated knowledge
        await self._initialize_ali_orchestrator()
        
        logger.info("✅ Ali ecosystem reloaded", total_agents=len(self.agents))
        
        return await self.get_ecosystem_status()