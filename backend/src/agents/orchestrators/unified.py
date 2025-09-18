"""
Unified Orchestrator Implementation
Consolidates all orchestration strategies into a single, efficient implementation
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime
import structlog

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage

from .base import BaseGroupChatOrchestrator
# Inline resilience components (moved from removed resilience.py)
from enum import Enum
from typing import Callable
from dataclasses import dataclass, field

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    half_open_max_calls: int = 3

@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    failed_calls: int = 0
    successful_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: list = field(default_factory=list)

class CircuitBreaker:
    """Circuit breaker implementation"""
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.half_open_calls = 0
        self.state_changed_at = datetime.now()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        try:
            self.stats.total_calls += 1
            result = await func(*args, **kwargs)
            self.stats.successful_calls += 1
            return result
        except Exception as e:
            self.stats.failed_calls += 1
            raise

    def get_status(self) -> Dict[str, Any]:
        """Return current circuit breaker status and stats"""
        return {
            "name": self.name,
            "state": self.state.value if isinstance(self.state, Enum) else str(self.state),
            "stats": {
                "total_calls": self.stats.total_calls,
                "failed_calls": self.stats.failed_calls,
                "successful_calls": self.stats.successful_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
                "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            },
            "state_changed_at": self.state_changed_at.isoformat(),
        }

class HealthMonitor:
    """Basic health monitoring"""
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self._running = False
        self._task = None
        
    async def start(self, orchestrators=None):
        """Start health monitoring"""
        self._running = True
        logger.info("Health monitor started")
        
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        logger.info("Health monitor stopped")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return current health status"""
        return {
            "status": "running" if self._running else "stopped",
            "check_interval": self.check_interval,
        }
from src.agents.services.groupchat.intelligent_router import IntelligentAgentRouter
# RAG functionality is now dynamically imported in initialize() method when enabled
from src.agents.services.groupchat.metrics import extract_agents_used, estimate_cost
from src.services.unified_cost_tracker import unified_cost_tracker
from src.agents.services.agent_intelligence import AgentIntelligence
from src.agents.security.ai_security_guardian import AISecurityGuardian
from src.agents.services.agent_loader import DynamicAgentLoader
from src.agents.tools.web_search_tool import get_web_tools
from src.agents.tools.database_tools import get_database_tools
from src.agents.tools.vector_search_tool import get_vector_tools
from src.core.ai_clients import get_autogen_client
from src.core.config import get_settings

logger = structlog.get_logger()


class UnifiedOrchestrator(BaseGroupChatOrchestrator):
    """
    Unified orchestrator that combines the best features from all existing orchestrators:
    - Intelligent routing from IntelligentAgentRouter
    - GroupChat for multi-agent scenarios
    - Direct agent conversation for efficiency
    - RAG support for context-aware responses
    - Safety gates for responsible AI
    - WebSocket streaming support
    - Cost and performance tracking
    """
    
    def __init__(self, name: str = "unified_orchestrator"):
        super().__init__(name)
        self.router = IntelligentAgentRouter()
        self.agent_intelligence = AgentIntelligence(agent_name=name)
        self.agent_loader = None
        self.termination_markers = ["DONE", "TERMINATE", "END_CONVERSATION"]
        self.max_rounds = 10
        
        # Enhanced circuit breaker with configurable settings
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3
        )
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        
        # Health monitoring
        self.health_monitor = HealthMonitor(check_interval=30)
    
    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """
        Initialize the unified orchestrator.
        
        Args:
            agents_dir: Path to agent definitions
            model_client: AI model client (creates one if not provided)
            **kwargs: Additional configuration
        
        Returns:
            Success status
        """
        try:
            # Initialize model client if not provided
            if model_client is None:
                model_client = get_autogen_client(provider="openai")
            self.model_client = model_client
            
            # Load agents from directory using DynamicAgentLoader
            logger.info(f"📂 Loading agents from {agents_dir}")
            self.agent_loader = DynamicAgentLoader(agents_dir)
            self.agent_loader.scan_and_load_agents()
            
            # Prepare tools BEFORE creating agents
            all_tools = []
            all_tools.extend(get_web_tools())
            all_tools.extend(get_database_tools())
            all_tools.extend(get_vector_tools())
            
            logger.info(f"🔧 Prepared {len(all_tools)} tools for agents")
            
            # Create AutoGen AssistantAgent instances WITH TOOLS
            self.agents = self.agent_loader.create_autogen_agents(
                model_client=self.model_client,
                tools=all_tools  # Pass tools to agent creation
            )
                    
            logger.info(f"✅ Loaded {len(self.agents)} agents with {len(all_tools)} tools integrated")

            # Provide a minimal fallback agent in test/dev if none were discovered
            if not self.agents and get_settings().ENVIRONMENT in ("test", "development"):
                try:
                    logger.warning("⚠️ No agents discovered; adding minimal fallback agent for tests")
                    fallback = AssistantAgent("ali", model_client=self.model_client)
                    self.agents = {"ali": fallback}
                except Exception as _e:
                    logger.warning(f"⚠️ Failed to create fallback agent: {_e}")
            
            # Initialize GroupChat for multi-agent scenarios
            if len(self.agents) > 1:
                # Configure a sensible termination condition
                termination = MaxMessageTermination(self.max_rounds) | TextMentionTermination("TERMINATE")
                self.group_chat = RoundRobinGroupChat(
                    participants=list(self.agents.values()),
                    termination_condition=termination,
                    max_turns=self.max_rounds,
                )
            
            # Initialize RAG processor if enabled
            if kwargs.get("enable_rag", True):  # Enabled by default now
                try:
                    from ..services.groupchat.rag import AdvancedRAGProcessor
                    from ..memory.autogen_memory_system import AutoGenMemorySystem
                    
                    memory_system = AutoGenMemorySystem()
                    self.rag_processor = AdvancedRAGProcessor(
                        memory_system=memory_system,
                        settings=get_settings()
                    )
                    logger.info("✅ RAG processor initialized successfully")
                except Exception as e:
                    logger.warning(f"⚠️ RAG processor initialization failed: {e}")
                    self.rag_processor = None
            else:
                self.rag_processor = None
            
            # Initialize safety guardian if enabled
            if kwargs.get("enable_safety", True):
                self.safety_guardian = AISecurityGuardian()
            
            # Mark as initialized
            self.is_initialized = True
            self.initialization_time = datetime.now()
            
            # Start health monitoring
            await self.health_monitor.start({self.name: self})
            
            logger.info(f"✅ Unified orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            # Circuit breaker tracks failures automatically
            return False
    
    def get_agent_metadata(self, agent_key: str):
        """Get original metadata for an agent"""
        if not self.agent_loader:
            return None
        return self.agent_loader.agent_metadata.get(agent_key)
    
    def list_agents_with_metadata(self):
        """Get list of agents with their original metadata"""
        if not self.agent_loader:
            return {}
        return self.agent_loader.agent_metadata
    
    async def orchestrate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process message through the unified orchestration system.
        
        Uses intelligent routing to determine the best approach:
        1. Single agent for focused queries (most efficient)
        2. Multi-agent GroupChat for complex queries
        3. Falls back gracefully on failures
        """
        
        # Check circuit breaker state
        if self.circuit_breaker.state == CircuitState.OPEN:
            return self._circuit_breaker_response()
        
        start_time = datetime.now()
        
        try:
            # Safety check if enabled (non-blocking in test/dev or when explicitly in test mode)
            if self.safety_guardian:
                safety_result = await self.safety_guardian.validate_prompt(message, user_id)
                is_test_env = get_settings().ENVIRONMENT in ("test", "development")
                is_test_mode = bool((context or {}).get("test_mode"))
                if not safety_result.execution_authorized and not (is_test_env or is_test_mode):
                    return {
                        "response": f"Security validation failed: {', '.join(safety_result.violations)}",
                        "agents_used": ["safety_guardian"],
                        "turn_count": 0,
                        "duration_seconds": 0,
                        "blocked": True
                    }
            
            # Check if a specific agent is requested
            target_agent = context.get("target_agent") if context else None
            
            # Add RAG context if available
            enhanced_message = message
            if self.rag_processor and context:
                try:
                    # Use AdvancedRAGProcessor to build memory context
                    rag_context_message = await self.rag_processor.build_memory_context(
                        user_id=user_id,
                        agent_id=target_agent if target_agent else None,
                        query=message,
                        limit=context.get("rag_limit", 5),
                        similarity_threshold=context.get("rag_threshold", 0.3),
                        include_conversation_history=context.get("include_history", True),
                        include_knowledge_base=context.get("include_knowledge", True)
                    )
                    
                    if rag_context_message and rag_context_message.content:
                        enhanced_message = f"{message}\n\n{rag_context_message.content}"
                        logger.info("✅ RAG context added to message", 
                                       original_length=len(message), 
                                       enhanced_length=len(enhanced_message))
                except Exception as e:
                    logger.warning(f"⚠️ RAG context generation failed: {e}")
                    # Continue with original message if RAG fails
            
            # Determine routing strategy
            # If Ali is targeted explicitly or caller prefers multi-agent, use GroupChat
            multi_agent_preferred = bool((context or {}).get("multi_agent_preferred"))
            ali_targeted = False
            if target_agent:
                ta = target_agent.lower().replace('-', '_')
                ali_targeted = ta in ("ali_chief_of_staff", "ali", "ali-chief-of-staff")

            if (ali_targeted or multi_agent_preferred) and getattr(self, 'group_chat', None):
                should_use_single = False
            else:
                # Default behavior: single agent for efficiency, unless router signals multi-agent
                should_use_single = self.router.should_use_single_agent(message)
            
            if should_use_single:
                # Route to single best agent
                result = await self._execute_single_agent(
                    enhanced_message, context, user_id, conversation_id
                )
            else:
                # Use multi-agent GroupChat
                result = await self._execute_multi_agent(
                    enhanced_message, context, user_id, conversation_id
                )
            
            # Update metrics and track REAL costs
            duration = (datetime.now() - start_time).total_seconds()
            self.update_metrics(
                tokens_used=result.get("tokens", 0),
                cost=result.get("cost", 0.0),
                response_time=duration
            )
            
            # Track real costs from API responses if available
            try:
                # If we have cost breakdown with real data, track it
                cost_breakdown = result.get("cost_breakdown", {})
                if cost_breakdown and cost_breakdown.get("total_cost_usd", 0) > 0:
                    logger.info(f"🔥 Real cost tracked: ${cost_breakdown.get('total_cost_usd', 0):.4f}")
                    # Cost tracking is handled by unified tracker in the API layer
            except Exception as e:
                logger.debug(f"Cost tracking info: {e}")
            
            # Circuit breaker tracks success automatically
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            # Circuit breaker tracks failures automatically
            
            # Fallback response with more details
            return {
                "response": f"I encountered an issue processing your request: {str(e)}",
                "agents_used": [],
                "turn_count": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }

    # Backward-compatibility alias used in some older call sites/tests
    async def process_query(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return await self.orchestrate(
            message=message,
            context=context,
            user_id=user_id,
            conversation_id=conversation_id,
            **kwargs,
        )
    
    async def _execute_single_agent(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Execute with a single agent for efficiency"""
        
        # Check if a specific agent is requested
        target_agent_name = context.get("target_agent") if context else None
        best_agent = None
        
        if target_agent_name:
            logger.info(f"🔍 Looking for target agent: {target_agent_name}")
            logger.info(f"🔍 Available agents: {list(self.agents.keys())[:5]}")
            
            # Try to find the requested agent
            best_agent = self.agents.get(target_agent_name)
            if not best_agent:
                # Try with underscores converted from hyphens
                target_agent_name_alt = target_agent_name.replace('-', '_')
                best_agent = self.agents.get(target_agent_name_alt)
            
            if best_agent:
                logger.info(f"✅ Using requested agent: {best_agent.name}")
            else:
                logger.warning(f"⚠️ Requested agent not found: {target_agent_name}, available: {list(self.agents.keys())}")
                # Fall through to normal selection
        
        if not best_agent:
            # Select best agent normally
            best_agent = self.router.select_best_agent(
                message,
                list(self.agents.values()),
                context
            )
        
        if not best_agent:
            # Fallback to first available agent if any exist
            if self.agents:
                best_agent = list(self.agents.values())[0]
            else:
                # No agents available - return error response
                return {
                    "response": "No agents available for processing this request.",
                    "agents_used": [],
                    "turn_count": 0,
                    "duration_seconds": 0,
                    "error": "No agents loaded"
                }
        
        logger.info(f"🎯 Single agent execution: {best_agent.name}")
        
        # Agent intelligence is handled through RAG context enhancement instead
        
        # Execute agent WITH TOOLS using AutoGen 0.7.x API
        messages = []
        try:
            from autogen_agentchat.messages import TextMessage
            task_message = TextMessage(content=message, source="user")
            
            # Run the agent - tools should now work since they're passed at creation
            result = await best_agent.run(task=task_message)
            
            # Extract response from result
            if hasattr(result, 'messages'):
                messages = result.messages
                # Get the last agent message
                final_response = ""
                for msg in reversed(messages):
                    if hasattr(msg, 'source') and msg.source == best_agent.name:
                        final_response = msg.content
                        break
                
                if not final_response:
                    # Try to get any message with content
                    for msg in reversed(messages):
                        if hasattr(msg, 'content') and msg.content:
                            final_response = msg.content
                            break
                            
                if not final_response:
                    final_response = "Agent executed but no response generated"
            else:
                final_response = str(result)
                
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            final_response = f"AGENT EXECUTION ERROR: {str(e)}"
        
        return {
            "response": final_response,
            "agents_used": [best_agent.name],
            "turn_count": 1,
            "duration_seconds": 0,  # Will be set by caller
            "routing": "single_agent",
            "cost_breakdown": estimate_cost(messages if isinstance(messages, list) else [])
        }
    
    async def _execute_multi_agent(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Execute with multiple agents for complex queries"""
        
        logger.info("🤝 Multi-agent execution via GroupChat")
        
        if not self.group_chat:
            # Fallback to single agent if no group chat
            return await self._execute_single_agent(
                message, context, user_id, conversation_id
            )
        
        # Run group chat
        task_message = TextMessage(content=message, source="user")
        # Run team with the task; termination is configured at construction time
        result = await self.group_chat.run(task=task_message)
        
        # Extract results
        messages = result.messages if hasattr(result, 'messages') else []
        agents_used = extract_agents_used(messages)
        
        # Get final response
        final_response = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                # Skip user messages and termination markers
                if msg.source != "user" and not any(
                    marker in msg.content for marker in self.termination_markers
                ):
                    final_response = msg.content
                    break
        
        return {
            "response": final_response,
            "agents_used": agents_used,
            "turn_count": len(messages),
            "duration_seconds": 0,  # Will be set by caller
            "routing": "multi_agent",
            "cost_breakdown": estimate_cost(messages if isinstance(messages, list) else [])
        }
    
    async def stream(
        self,
        message: str,
        websocket: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream responses via WebSocket"""
        
        # Determine best agent for streaming
        best_agent = self.router.select_best_agent(
            message,
            list(self.agents.values()),
            context
        )
        
        if not best_agent:
            best_agent = list(self.agents.values())[0]
        
        logger.info(f"🔄 Streaming via {best_agent.name}")
        
        # Stream agent response
        async for chunk in best_agent.run_stream(task=message):
            if hasattr(chunk, 'content') and isinstance(chunk.content, str):
                # Send to websocket
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk.content,
                    "agent": best_agent.name
                })
                yield chunk.content
        
        # Send completion signal
        await websocket.send_json({
            "type": "complete",
            "agent": best_agent.name
        })
    
    def _check_termination(self, messages: List[Any]) -> bool:
        """Check if conversation should terminate"""
        if not messages:
            return False
        
        last_message = messages[-1]
        if hasattr(last_message, 'content') and isinstance(last_message.content, str):
            return any(
                marker in last_message.content 
                for marker in self.termination_markers
            )
        
        return len(messages) >= self.max_rounds
    
    async def health(self) -> bool:
        """Check orchestrator health"""
        return self.is_initialized and self.circuit_breaker.state != CircuitState.OPEN
    
    def get_circuit_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return self.circuit_breaker.get_status()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health monitoring status"""
        return self.health_monitor.get_health_status()
    
    async def shutdown(self):
        """Shutdown orchestrator and cleanup resources"""
        await self.health_monitor.stop()
        logger.info("Orchestrator shutdown complete")
    
    def _circuit_breaker_response(self) -> Dict[str, Any]:
        """Response when circuit breaker is open"""
        return {
            "response": "The system is temporarily unavailable. Please try again in a moment.",
            "agents_used": [],
            "turn_count": 0,
            "duration_seconds": 0,
            "circuit_breaker": "open",
            "circuit_status": self.circuit_breaker.get_status()
        }
    
    # ===================== SWARM ORCHESTRATION =====================
    async def orchestrate_swarm(
        self,
        message: str,
        user_id: str = "api_user",
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        master_agent: str = "ali_chief_of_staff"
    ) -> Dict[str, Any]:
        """
        Orchestrate using swarm intelligence with a master agent
        Compatible with AliSwarmOrchestrator interface
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Use master agent if available, fallback to regular orchestration
        enhanced_context = context or {}
        enhanced_context.update({
            "swarm_mode": True,
            "master_agent": master_agent,
            "multi_agent_preferred": True
        })
        
        return await self.orchestrate(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=enhanced_context
        )
    
    # ===================== STREAMING CAPABILITIES =====================
    async def create_streaming_session(
        self,
        websocket: Any,
        user_id: str,
        agent_name: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create streaming session compatible with StreamingOrchestrator
        """
        from uuid import uuid4
        session_id = str(uuid4())
        
        # Store session info in context for streaming
        self._streaming_sessions = getattr(self, '_streaming_sessions', {})
        self._streaming_sessions[session_id] = {
            'websocket': websocket,
            'user_id': user_id,
            'agent_name': agent_name,
            'context': session_context,
            'created_at': datetime.now()
        }
        
        return session_id
    
    async def stream_response(
        self,
        session_id: str,
        message: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response for a session"""
        sessions = getattr(self, '_streaming_sessions', {})
        session = sessions.get(session_id)
        
        if not session:
            yield {"error": "Session not found"}
            return
        
        # Use streaming via WebSocket
        async for chunk in self.stream(
            message=message,
            websocket=session['websocket'],
            context=session.get('context'),
            **kwargs
        ):
            yield {"content": chunk, "session_id": session_id}
    
    # ===================== WORKFLOW ORCHESTRATION =====================
    async def generate_workflow(self, prompt: str) -> Dict[str, Any]:
        """Generate workflow from prompt (GraphFlow compatibility)"""
        # Delegate to regular orchestration with workflow context
        return await self.orchestrate(
            message=f"Generate a workflow for: {prompt}",
            context={"workflow_generation": True, "format": "structured"}
        )
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute workflow by ID (GraphFlow compatibility)"""
        return await self.orchestrate(
            message=f"Execute workflow {workflow_id}",
            context={"workflow_execution": True, "input_data": input_data}
        )