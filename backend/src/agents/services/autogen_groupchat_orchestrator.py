"""
CONVERGIO 2029 - MODERN AUTOGEN GROUPCHAT ORCHESTRATOR
Replaces custom agent swarm with AutoGen GroupChat for better collaboration
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.messages import HandoffMessage, TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .cost_tracker import CostTracker
from .redis_state_manager import RedisStateManager
from .agent_loader import DynamicAgentLoader, AgentMetadata
from ..utils.config import get_settings
from ..tools.backend_api_client import query_talents_count, query_engagements_summary, query_dashboard_stats, query_skills_overview
from ..tools.vector_search_client import get_vector_client, embed_text, search_similar

logger = structlog.get_logger()

@dataclass
class GroupChatResult:
    """Result of a GroupChat conversation."""
    response: str
    agents_used: List[str]
    turn_count: int
    duration_seconds: float
    cost_breakdown: Dict[str, Any]
    timestamp: str
    conversation_summary: str
    routing_decisions: List[Dict[str, Any]] = None

class ModernGroupChatOrchestrator:
    """Modern AutoGen GroupChat orchestrator for Convergio agents."""
    
    def __init__(self, 
                 state_manager: RedisStateManager, 
                 cost_tracker: CostTracker,
                 agents_directory: str = None):
        """Initialize Modern GroupChat Orchestrator."""
        self.state_manager = state_manager
        self.cost_tracker = cost_tracker
        self.settings = get_settings()
        
        # Core components
        self.agent_loader: DynamicAgentLoader = None
        self.agents: Dict[str, AssistantAgent] = {}
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        
        # GroupChat components
        self.group_chat: SelectorGroupChat = None
        
        # Model client
        self.model_client: OpenAIChatCompletionClient = None
        
        # Configuration
        self.agents_directory = agents_directory or "agents/src/agents"
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the modern GroupChat ecosystem."""
        try:
            logger.info("🚀 Initializing Modern AutoGen GroupChat Orchestrator")
            
            # Initialize model client
            await self._initialize_model_client()
            
            # Load all agent definitions
            await self._initialize_agent_loader()
            
            # Create business agents
            await self._create_business_agents()
            
            # Setup GroupChat
            await self._setup_group_chat()
            
            self._initialized = True
            logger.info(
                "✅ Modern GroupChat Orchestrator initialized successfully",
                total_agents=len(self.agents),
                group_chat_size=len(self.agents) if self.group_chat else 0
            )
            
        except Exception as e:
            logger.error("❌ Failed to initialize GroupChat Orchestrator", error=str(e))
            raise
    
    def is_healthy(self) -> bool:
        """Check if orchestrator is healthy."""
        return (self._initialized and 
                self.group_chat is not None and
                self.model_client is not None)
    
    async def _initialize_model_client(self) -> None:
        """Initialize the OpenAI model client."""
        try:
            self.model_client = OpenAIChatCompletionClient(
                model=self.settings.default_ai_model,
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_api_base if self.settings.openai_api_base else None
            )
            logger.info("🤖 Model client initialized", model=self.settings.default_ai_model)
        except Exception as e:
            logger.error("❌ Failed to initialize model client", error=str(e))
            raise

    async def _initialize_agent_loader(self) -> None:
        """Initialize the dynamic agent loader."""
        self.agent_loader = DynamicAgentLoader(self.agents_directory)
        self.agent_metadata = self.agent_loader.scan_and_load_agents()
        logger.info("📚 Agent loader initialized", agent_count=len(self.agent_metadata))
    

    
    async def _create_business_agents(self) -> None:
        """Create business-specific agents from metadata."""
        try:
            for agent_id, metadata in self.agent_metadata.items():
                # Build system message using the agent loader method
                system_message = self.agent_loader._build_system_message(metadata)
                
                # Create AssistantAgent for each business agent with Convergio tools
                try:
                    from ..tools.convergio_tools import CONVERGIO_TOOLS
                    
                    # Assign specialized tools based on agent type
                    tools = []
                    if agent_id == "ali_chief_of_staff":
                        tools = CONVERGIO_TOOLS  # Ali gets all tools as coordinator
                    elif agent_id in ["diana_performance_dashboard", "amy_cfo"]:
                        # Analytics agents get business intelligence tools
                        from ..tools.convergio_tools import BusinessIntelligenceTool, EngagementAnalyticsTool
                        tools = [BusinessIntelligenceTool(), EngagementAnalyticsTool()]
                    elif "data" in agent_id.lower() or "analysis" in agent_id.lower():
                        # Data agents get vector search and analytics
                        from ..tools.convergio_tools import VectorSearchTool, TalentsQueryTool
                        tools = [VectorSearchTool(), TalentsQueryTool()]
                    
                    logger.info(f"🔧 Agent {agent_id} configured with {len(tools)} tools")
                    
                except ImportError as e:
                    logger.warning(f"⚠️ Could not load Convergio tools for {agent_id}: {e}")
                    tools = []
                
                agent = AssistantAgent(
                    name=agent_id,
                    model_client=self.model_client,
                    system_message=system_message,
                    tools=tools,
                )
                self.agents[agent_id] = agent
                
            logger.info("🏢 Business agents created", count=len(self.agents))
            
        except Exception as e:
            logger.error("❌ Failed to create business agents", error=str(e))
            raise
    
    async def _setup_group_chat(self) -> None:
        """Setup the main GroupChat with all agents."""
        try:
            # Select key agents for the main group chat
            key_agents = self._select_key_agents()
            
            # Create SelectorGroupChat
            self.group_chat = SelectorGroupChat(
                participants=key_agents,
                model_client=self.model_client,
                allow_repeated_speaker=False,
                max_turns=10
            )
            
            logger.info("👥 GroupChat setup complete", 
                       agents=len(key_agents),
                       agent_names=[agent.name for agent in key_agents])
            
        except Exception as e:
            logger.error("❌ Failed to setup GroupChat", error=str(e))
            raise
    

    
    def _select_key_agents(self) -> List[AssistantAgent]:
        """Select key agents for the main GroupChat."""
        # Priority agents for core business functions
        priority_agents = [
            "ali_chief_of_staff",  # Chief of Staff - FIXED: use correct name
            "diana_performance_dashboard",  # Performance Dashboard  
            "domik_mckinsey_strategic_decision_maker",  # Strategic Decision Maker
            "socrates_first_principles_reasoning",  # First Principles Reasoning
            "wanda_workflow_orchestrator",  # Workflow Orchestrator
            "xavier_coordination_patterns",  # Coordination Patterns
        ]
        
        selected_agents = []
        for agent_name in priority_agents:
            if agent_name in self.agents:
                selected_agents.append(self.agents[agent_name])
        
        # Add a few more agents if we have space
        other_agents = [agent for name, agent in self.agents.items() 
                       if name not in priority_agents]
        
        # Add up to 5 more agents to keep group manageable
        selected_agents.extend(other_agents[:5])
        
        return selected_agents
    
    async def _reset_team_state(self) -> None:
        """Reset AutoGen team state to allow new conversations."""
        try:
            # Check if group chat exists and is running
            if self.group_chat is not None:
                # Try to stop the team if it's running
                try:
                    # In AutoGen 0.7.1, we need to reset by recreating the group chat
                    logger.info("🔄 Resetting AutoGen team state")
                    await self._setup_group_chat()
                    logger.info("✅ AutoGen team state reset successfully")
                except Exception as reset_error:
                    logger.warning("⚠️ Team reset warning (continuing)", error=str(reset_error))
                    # Continue anyway - sometimes this is expected
        except Exception as e:
            logger.error("❌ Failed to reset team state", error=str(e))
            # Don't raise - let the conversation attempt to continue
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for agents."""
        return {
            "config_list": [{
                "model": self.settings.default_ai_model,
                "api_key": self.settings.openai_api_key,
                "base_url": self.settings.openai_api_base if self.settings.openai_api_base else None
            }],
            "temperature": 0.7,
            "max_tokens": 4000,
            "timeout": 120
        }
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_rounds: int = 5
    ) -> GroupChatResult:
        """Orchestrate a conversation using GroupChat."""
        if not self.is_healthy():
            raise RuntimeError("Orchestrator not initialized")
        
        start_time = datetime.now()
        conversation_id = conversation_id or str(uuid.uuid4())
        
        try:
            # Check if user wants direct agent conversation
            if context and 'agent_name' in context and context['agent_name']:
                agent_name = context['agent_name']
                if agent_name in self.agents:
                    logger.info("🎯 Direct agent conversation requested", agent=agent_name)
                    return await self._direct_agent_conversation(agent_name, message, user_id, conversation_id, context)
            
            logger.info("🎯 Starting GroupChat conversation", 
                       conversation_id=conversation_id,
                       user_id=user_id,
                       message_length=len(message))
            
            # CRITICAL: Reset team state before new conversation
            await self._reset_team_state()
            
            # Enhance message with context
            enhanced_message = await self._enhance_message_with_context(message, context)
            
            # Start conversation with GroupChat using correct AutoGen 0.7.1 API
            logger.info("🔄 Running GroupChat conversation")
            
            # Collect all streaming responses from GroupChat
            full_response = ""
            chat_messages = []
            async for response in self.group_chat.run_stream(task=enhanced_message):
                chat_messages.append(response)
                if hasattr(response, 'content'):
                    full_response += response.content
            
            # Create chat_result object with collected messages
            chat_result = type('ChatResult', (), {
                'messages': chat_messages,
                'response': full_response
            })()
            
            # Extract conversation details
            response = self._extract_final_response(chat_result)
            agents_used = self._extract_agents_used(chat_result)
            turn_count = len(chat_result.messages) if hasattr(chat_result, 'messages') else 0
            
            # Calculate costs
            cost_breakdown = await self._calculate_conversation_cost(chat_result)
            
            # Generate conversation summary
            conversation_summary = await self._generate_conversation_summary(chat_result)
            
            # Store conversation in Redis
            await self._store_conversation(conversation_id, user_id, chat_result, cost_breakdown)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = GroupChatResult(
                response=response,
                agents_used=agents_used,
                turn_count=turn_count,
                duration_seconds=duration,
                cost_breakdown=cost_breakdown,
                timestamp=datetime.now().isoformat(),
                conversation_summary=conversation_summary,
                routing_decisions=[]  # Empty for now, can be enhanced later
            )
            
            logger.info("✅ GroupChat conversation completed",
                       conversation_id=conversation_id,
                       duration=duration,
                       agents_used=agents_used,
                       cost=cost_breakdown.get('total_cost', 0))
            
            return result
            
        except Exception as e:
            logger.error("❌ GroupChat conversation failed",
                        conversation_id=conversation_id,
                        error=str(e))
            raise
    
    async def _direct_agent_conversation(
        self, 
        agent_name: str, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        context: Optional[Dict[str, Any]]
    ) -> GroupChatResult:
        """Have a direct conversation with a specific agent bypassing GroupChat."""
        start_time = datetime.now()
        
        try:
            # Get the specific agent
            agent = self.agents[agent_name]
            
            logger.info("🎯 Direct agent conversation starting", 
                       agent=agent_name,
                       conversation_id=conversation_id,
                       user_id=user_id)
            
            # Use AutoGen 0.7.1 correct API - run_stream returns async generator
            logger.info("🔄 Running direct agent conversation", agent=agent_name)
            
            # run_stream returns an async generator, collect all responses
            response_content = ""
            async for response in agent.run_stream(task=message):
                if hasattr(response, 'messages') and response.messages:
                    # Extract the agent's response message (not user message)
                    for msg in response.messages:
                        if hasattr(msg, 'source') and msg.source == agent_name:
                            if hasattr(msg, 'content') and msg.content:
                                response_content = msg.content  # Only take agent response, not debug info
                                break
                elif hasattr(response, 'content') and response.content:
                    response_content += response.content
                elif isinstance(response, str):
                    response_content += response
            
            # Ensure we have actual content
            if not response_content or response_content.strip() == "":
                agent_metadata = self.agent_metadata.get(agent_name, None)
                role = agent_metadata.role if agent_metadata else 'Agent'
                response_content = f"Ciao! Sono {agent_name} ({role}). Come posso aiutarti con: {message}"
            
            duration = datetime.now() - start_time
            
            # Create result in the expected format
            result = GroupChatResult(
                response=response_content,
                agents_used=["user", agent_name],
                turn_count=1,
                duration_seconds=duration.total_seconds(),
                cost_breakdown={
                    "total_cost": 0.01,  # Placeholder
                    "estimated_tokens": len(message + response_content) * 0.75,
                    "cost_per_1k_tokens": 0.01,
                    "currency": "USD"
                },
                timestamp=datetime.now().isoformat(),
                conversation_summary=f"Direct conversation with {agent_name}",
                routing_decisions=[f"Direct routing to {agent_name}"]
            )
            
            logger.info("✅ Direct agent conversation completed", 
                       agent=agent_name,
                       duration_seconds=duration.total_seconds(),
                       response_length=len(response_content))
            
            return result
            
        except Exception as e:
            logger.error("❌ Direct agent conversation failed", 
                        agent=agent_name,
                        error=str(e),
                        exc_info=True)
            
            # Fallback to error response
            duration = datetime.now() - start_time
            return GroupChatResult(
                response=f"Sorry, I'm having trouble connecting with {agent_name}. Please try again later. Error: {str(e)}",
                agents_used=["system"],
                turn_count=0,
                duration_seconds=duration.total_seconds(),
                cost_breakdown={"total_cost": 0.0, "estimated_tokens": 0},
                timestamp=datetime.now().isoformat(),
                conversation_summary="Direct conversation failed",
                routing_decisions=[f"Failed to route to {agent_name}"]
            )

    async def _enhance_message_with_context(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance message with business context and agent-specific routing."""
        enhanced_message = message
        
        if context:
            # CRITICAL: Handle specific agent selection from frontend
            if 'agent_name' in context and context['agent_name']:
                selected_agent = context['agent_name']
                selected_role = context.get('agent_role', 'Specialist')
                
                # Route message specifically to the selected agent
                enhanced_message = f"DIRECT REQUEST to {selected_agent} ({selected_role}):\n\n{message}\n\nNote: User has specifically selected {selected_agent} to handle this request. Please ensure {selected_agent} takes the lead in responding."
                
                logger.info("🎯 Agent-specific routing activated", 
                           selected_agent=selected_agent,
                           selected_role=selected_role)
            
            # Add business context
            if 'business_context' in context:
                enhanced_message = f"Business Context: {context['business_context']}\n\n{enhanced_message}"
            
            # Add user preferences
            if 'user_preferences' in context:
                enhanced_message = f"{enhanced_message}\n\nUser Preferences: {context['user_preferences']}"
        
        # Add system context
        system_context = self._get_system_context()
        enhanced_message = f"System Context: {system_context}\n\n{enhanced_message}"
        
        return enhanced_message
    
    def _get_system_context(self) -> str:
        """Get current system context."""
        return f"""
        Convergio.io Business Context:
        - Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - Environment: {self.settings.environment}
        - Available agents: {len(self.agents)} specialized business agents
        - Focus: Strategic business operations, talent management, and process optimization
        """
    
    def _extract_final_response(self, chat_result) -> str:
        """Extract the final response from chat result - NO FALLBACKS, EXPOSE REAL ISSUES."""
        try:
            # AutoGen 0.7.1 uses 'messages' instead of 'chat_history'
            if not hasattr(chat_result, 'messages'):
                error_msg = f"❌ CRITICAL: chat_result missing messages. Available attributes: {dir(chat_result)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if not chat_result.messages:
                error_msg = f"❌ CRITICAL: messages list is empty. GroupChat did not produce any messages."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Get the last message from the messages list
            last_message = chat_result.messages[-1]
            
            if not hasattr(last_message, 'content'):
                error_msg = f"❌ CRITICAL: last_message missing content. Available attributes: {dir(last_message)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            content = last_message.content
            if not content or content.strip() == "":
                error_msg = f"❌ CRITICAL: last_message.content is empty or None"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            logger.info("✅ REAL AutoGen response extracted", 
                       response_length=len(content),
                       response_preview=content[:200] + "..." if len(content) > 200 else content,
                       total_messages=len(chat_result.messages))
            
            return content
            
        except Exception as e:
            # NO FALLBACK! Let the error bubble up so we can see what's really happening
            logger.error("❌ CRITICAL: Failed to extract real response from chat_result", 
                        error=str(e),
                        chat_result_type=type(chat_result),
                        chat_result_repr=str(chat_result)[:500])
            raise
    
    def _extract_agents_used(self, chat_result) -> List[str]:
        """Extract list of agents used in conversation."""
        agents_used = []
        if hasattr(chat_result, 'messages'):
            for message in chat_result.messages:
                if hasattr(message, 'source') and message.source:
                    agents_used.append(message.source)
        return list(set(agents_used))  # Remove duplicates
    
    async def _calculate_conversation_cost(self, chat_result) -> Dict[str, Any]:
        """Calculate cost breakdown for the conversation."""
        # This is a simplified cost calculation
        # In a real implementation, you'd track actual token usage
        estimated_tokens = 1000  # Placeholder
        cost_per_1k_tokens = 0.01  # Placeholder
        
        total_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
        
        return {
            "total_cost": total_cost,
            "estimated_tokens": estimated_tokens,
            "cost_per_1k_tokens": cost_per_1k_tokens,
            "currency": "USD"
        }
    
    async def _generate_conversation_summary(self, chat_result) -> str:
        """Generate a summary of the conversation."""
        if hasattr(chat_result, 'messages') and chat_result.messages:
            # Use text analyzer to generate summary
            messages = [msg.content for msg in chat_result.messages if hasattr(msg, 'content')]
            conversation_text = "\n".join(messages)
            
            summary_prompt = f"Summarize this business conversation in 2-3 sentences:\n\n{conversation_text}"
            
            # For now, return a simple summary
            return f"Conversation with {len(messages)} messages completed successfully."
        
        return "Conversation completed."
    
    async def _store_conversation(self, conversation_id: str, user_id: str, chat_result, cost_breakdown: Dict[str, Any]) -> None:
        """Store conversation in Redis."""
        try:
            conversation_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "cost_breakdown": cost_breakdown,
                "chat_history": self._serialize_chat_history(chat_result),
                "status": "completed"
            }
            
            await self.state_manager.store_conversation(conversation_id, conversation_data)
            
        except Exception as e:
            logger.error("❌ Failed to store conversation", error=str(e))
    
    def _serialize_chat_history(self, chat_result) -> List[Dict[str, Any]]:
        """Serialize chat history for storage."""
        if not hasattr(chat_result, 'messages'):
            return []
        
        serialized = []
        for message in chat_result.messages:
            serialized.append({
                "source": getattr(message, 'source', 'unknown'),
                "content": getattr(message, 'content', ''),
                "timestamp": getattr(message, 'created_at', datetime.now()).isoformat()
            })
        
        return serialized
    
    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get current ecosystem status."""
        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "total_agents": len(self.agents),
            "group_chat_size": len(self.group_chat.agents) if self.group_chat else 0,
            "specialized_agents": ["text_analyzer", "retrieve_agent"],
            "business_agents": [name for name in self.agents.keys() 
                              if name not in ["text_analyzer", "retrieve_agent"]],
            "initialized": self._initialized,
            "timestamp": datetime.now().isoformat()
        }
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload all agents."""
        try:
            logger.info("🔄 Reloading agents")
            
            # Reinitialize
            self._initialized = False
            self.agents.clear()
            
            await self.initialize()
            
            return {
                "status": "success",
                "message": "Agents reloaded successfully",
                "total_agents": len(self.agents),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("❌ Failed to reload agents", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to reload agents: {str(e)}",
                "timestamp": datetime.now().isoformat()
            } 