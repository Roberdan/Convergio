"""
Agent Framework Orchestrator - Next-Generation Orchestration
Replaces AutoGen-based UnifiedOrchestrator with Microsoft Agent Framework
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import structlog

try:
    from agent_framework import (
        ChatAgent,
        Workflow,
        WorkflowBuilder,
        WorkflowContext,
        executor,
        Case,
        Default,
        AgentExecutor,
        AgentExecutorRequest,
        AgentExecutorResponse,
        ChatMessage,
        Role
    )
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    # Fallback to compatibility layer
    Workflow = None
    WorkflowBuilder = None
    ChatAgent = None

from .base import BaseGroupChatOrchestrator
from src.agents.services.groupchat.intelligent_router import IntelligentAgentRouter
from src.agents.services.groupchat.metrics import extract_agents_used, estimate_cost
from src.services.unified_cost_tracker import unified_cost_tracker
from src.agents.services.agent_intelligence import AgentIntelligence
from src.agents.security.ai_security_guardian import AISecurityGuardian
from src.core.agent_framework_config import get_agent_framework_config, get_checkpoint_store
from src.core.config import get_settings

logger = structlog.get_logger()


class AgentFrameworkOrchestrator(BaseGroupChatOrchestrator):
    """
    Next-generation orchestrator using Microsoft Agent Framework.

    Features:
    - Graph-based workflow orchestration (vs event-driven)
    - ChatAgent with multi-turn by default (vs AssistantAgent)
    - Checkpointing and workflow resumption
    - Parallel agent execution
    - Human-in-the-loop capabilities
    - Advanced routing with conditional edges
    - Full observability and telemetry
    """

    def __init__(self, name: str = "agent_framework_orchestrator"):
        super().__init__(name)

        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError(
                "Microsoft Agent Framework not installed. "
                "Install with: pip install agent-framework --pre"
            )

        self.router = IntelligentAgentRouter()
        self.agent_intelligence = AgentIntelligence(agent_name=name)
        self.config = get_agent_framework_config()

        # Workflow components
        self.workflow: Optional[Workflow] = None
        self.checkpoint_store = None

        # Agent registry
        self.agents: Dict[str, ChatAgent] = {}
        self.agent_executors: Dict[str, AgentExecutor] = {}
        self.agent_metadata: Dict[str, Any] = {}

        # Configuration
        self.termination_markers = ["DONE", "TERMINATE", "END_CONVERSATION"]
        self.max_workflow_iterations = self.config.max_workflow_iterations

        # Safety
        self.safety_guardian = None

        # Routing context for workflow
        self.routing_context: Dict[str, Any] = {}

        logger.info("Agent Framework Orchestrator initialized", name=name)

    async def initialize(
        self,
        agents: Dict[str, ChatAgent],
        agent_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Initialize orchestrator with agents and configuration.

        Args:
            agents: Dictionary of ChatAgent instances
            agent_metadata: Optional metadata about agents
            **kwargs: Additional configuration

        Returns:
            Success status
        """
        try:
            self.agents = agents
            self.agent_metadata = agent_metadata or {}

            logger.info(f"Initializing with {len(agents)} agents")

            # Create AgentExecutor wrappers for all agents
            for agent_name, agent in agents.items():
                self.agent_executors[agent_name] = AgentExecutor(agent, id=agent_name)

            # Initialize checkpoint store if enabled
            if self.config.enable_checkpointing:
                self.checkpoint_store = get_checkpoint_store(self.config)

            # Initialize workflow
            self.workflow = self._build_workflow()

            # Initialize safety guardian if enabled
            if kwargs.get("enable_safety", True) and self.config.enable_safety_checks:
                self.safety_guardian = AISecurityGuardian()

            self.is_initialized = True
            self.initialization_time = datetime.now()

            logger.info("Agent Framework Orchestrator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return False

    def _build_workflow(self) -> Workflow:
        """
        Build the workflow graph with agents and routing logic using WorkflowBuilder.

        Returns:
            Configured Workflow instance
        """
        builder = WorkflowBuilder()

        # Create custom executors using the @executor decorator pattern
        # We'll define them as instance methods that return executor functions

        # Start executor
        @executor(id="start")
        async def start_executor(message: str, ctx: WorkflowContext[str]) -> None:
            """Entry point - analyze and route the message"""
            logger.info("Workflow started", message_length=len(message))

            # Store context
            await ctx.set_shared_state("start_time", datetime.now().isoformat())
            await ctx.set_shared_state("original_message", message)
            await ctx.set_shared_state("agents_executed", [])

            # Determine routing
            target_agent = self.routing_context.get("target_agent")

            # Check for explicit Ali targeting
            if target_agent:
                ta = target_agent.lower().replace('-', '_')
                if ta in ("ali_chief_of_staff", "ali", "ali-chief-of-staff"):
                    await ctx.set_shared_state("routing_decision", "ali")
                    # Send to Ali
                    if "ali_chief_of_staff" in self.agent_executors:
                        await ctx.send_message(
                            AgentExecutorRequest(
                                messages=[ChatMessage(Role.USER, text=message)],
                                should_respond=True
                            )
                        )
                    return

            # Use intelligent router
            should_use_single = self.router.should_use_single_agent(message)

            if should_use_single:
                # Select best agent
                best_agent = self.router.select_best_agent(
                    message,
                    list(self.agents.values()),
                    self.routing_context
                )

                if best_agent:
                    await ctx.set_shared_state("routing_decision", "single")
                    await ctx.set_shared_state("selected_agent", best_agent.name)

                    # Send to the selected agent
                    if best_agent.name in self.agent_executors:
                        await ctx.send_message(
                            AgentExecutorRequest(
                                messages=[ChatMessage(Role.USER, text=message)],
                                should_respond=True
                            )
                        )
            else:
                # Multi-agent mode - send to Ali for orchestration
                await ctx.set_shared_state("routing_decision", "multi")
                if "ali_chief_of_staff" in self.agent_executors:
                    await ctx.send_message(
                        AgentExecutorRequest(
                            messages=[ChatMessage(Role.USER, text=message)],
                            should_respond=True
                        )
                    )

        # Completion executor
        @executor(id="complete")
        async def complete_executor(response: AgentExecutorResponse, ctx: WorkflowContext[None, str]) -> None:
            """Finalize and output the result"""
            # Extract response text
            response_text = response.agent_run_response.text if hasattr(response.agent_run_response, 'text') else str(response)

            # Get metadata
            start_time_str: str = await ctx.get_shared_state("start_time") or datetime.now().isoformat()
            agents_executed: list = await ctx.get_shared_state("agents_executed") or []

            # Yield final output
            await ctx.yield_output(response_text)

            logger.info(
                "Workflow completed",
                agents_executed=len(agents_executed)
            )

        # Build workflow
        builder.set_start_executor(start_executor)

        # Add agent executors
        for agent_name, agent_executor in self.agent_executors.items():
            # Connect start to each agent (routing handled in start executor)
            builder.add_edge(start_executor, agent_executor)
            # Connect each agent to completion
            builder.add_edge(agent_executor, complete_executor)

        # Add checkpointing if enabled
        if self.config.enable_checkpointing and self.checkpoint_store:
            builder.with_checkpointing(self.checkpoint_store)

        # Set max iterations
        builder.set_max_iterations(self.max_workflow_iterations)

        workflow = builder.build()

        logger.info(f"Workflow built with {len(self.agent_executors)} agent executors")

        return workflow


    async def orchestrate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Orchestrate request using Agent Framework - direct agent execution.

        Args:
            message: Input message
            context: Optional context
            user_id: User identifier
            conversation_id: Conversation identifier

        Returns:
            Orchestration result
        """
        start_time = datetime.now()
        agents_used = []
        cost_breakdown = {"input_tokens": 0, "output_tokens": 0, "total_cost_usd": 0.0}

        try:
            # Safety check if enabled
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
                        "blocked": True,
                        "cost_breakdown": cost_breakdown
                    }

            # Determine target agent
            target_agent_key = None
            if context and context.get("target_agent"):
                ta = context["target_agent"].lower().replace('-', '_')
                if ta in self.agents:
                    target_agent_key = ta
                elif f"{ta}_chief_of_staff" in self.agents:
                    target_agent_key = f"{ta}_chief_of_staff"

            # Use intelligent router to select best agent if no target specified
            if not target_agent_key:
                best_agent = self.router.select_best_agent(
                    message,
                    list(self.agents.values()),
                    context
                )
                if best_agent and hasattr(best_agent, 'name'):
                    target_agent_key = best_agent.name

            # Fallback to Ali if no agent selected
            if not target_agent_key:
                target_agent_key = "ali_chief_of_staff" if "ali_chief_of_staff" in self.agents else list(self.agents.keys())[0]

            # Get the agent
            agent = self.agents.get(target_agent_key)
            if not agent:
                return {
                    "response": f"Agent not found: {target_agent_key}",
                    "agents_used": [],
                    "turn_count": 0,
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                    "error": "Agent not found",
                    "cost_breakdown": cost_breakdown
                }

            logger.info(f"🎯 Routing to agent: {target_agent_key}", message_preview=message[:50])
            agents_used.append(target_agent_key)

            # Execute agent directly using ChatAgent.run()
            response = await agent.run(messages=message)

            # Extract response text
            if hasattr(response, 'text'):
                final_response = response.text
            elif hasattr(response, 'content'):
                final_response = response.content
            elif isinstance(response, str):
                final_response = response
            else:
                final_response = str(response)

            # Track cost using unified tracker
            try:
                await unified_cost_tracker.track_cost(
                    agent_name=target_agent_key,
                    model="gpt-4o-mini",
                    input_tokens=len(message.split()) * 2,  # Estimate
                    output_tokens=len(final_response.split()) * 2,  # Estimate
                    user_id=user_id
                )
                cost_breakdown = {
                    "input_tokens": len(message.split()) * 2,
                    "output_tokens": len(final_response.split()) * 2,
                    "total_cost_usd": (len(message.split()) * 2 * 0.00015 + len(final_response.split()) * 2 * 0.0006) / 1000
                }
            except Exception as cost_err:
                logger.warning(f"Cost tracking failed: {cost_err}")

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "response": final_response,
                "agents_used": agents_used,
                "turn_count": len(agents_used),
                "duration_seconds": duration,
                "execution_mode": "direct",
                "cost_breakdown": cost_breakdown
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)

            return {
                "response": f"I encountered an issue processing your request: {str(e)}",
                "agents_used": agents_used,
                "turn_count": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": str(e),
                "cost_breakdown": cost_breakdown
            }

    async def stream(
        self,
        message: str,
        websocket: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream responses via WebSocket.

        Args:
            message: Input message
            websocket: WebSocket connection
            context: Optional context

        Yields:
            Response chunks
        """
        # Determine best agent for streaming
        best_agent = self.router.select_best_agent(
            message,
            list(self.agents.values()),
            context
        )

        if not best_agent:
            best_agent = list(self.agents.values())[0] if self.agents else None

        if not best_agent:
            await websocket.send_json({"type": "error", "content": "No agents available"})
            return

        logger.info(f"Streaming via {best_agent.name}")

        # Stream agent response using workflow
        try:
            # Use workflow streaming if available
            async for event in self.workflow.run_stream(message):
                # Handle different event types
                event_data = str(event)
                if event_data:
                    await websocket.send_json({
                        "type": "chunk",
                        "content": event_data,
                        "agent": best_agent.name if best_agent else "unknown"
                    })
                    yield event_data

            await websocket.send_json({
                "type": "complete",
                "agent": best_agent.name if best_agent else "workflow"
            })

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })

    async def health(self) -> bool:
        """Check orchestrator health"""
        return self.is_initialized and self.workflow is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "name": self.name,
            "initialized": self.is_initialized,
            "agents_count": len(self.agents),
            "workflow_max_iterations": self.max_workflow_iterations,
            "checkpointing_enabled": self.config.enable_checkpointing,
            "framework": "Microsoft Agent Framework"
        }

    def get_agent_metadata(self, agent_key: str) -> Optional[Any]:
        """Get original metadata for an agent."""
        return self.agent_metadata.get(agent_key)

    def list_agents_with_metadata(self) -> Dict[str, Any]:
        """Get list of agents with their original metadata."""
        return {
            key: {
                "agent": self.agents.get(key),
                "metadata": self.agent_metadata.get(key)
            }
            for key in self.agents.keys()
        }

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and cleanup resources."""
        logger.info("Shutting down Agent Framework Orchestrator")
        self.agents.clear()
        self.agent_executors.clear()
        self.workflow = None
        self.is_initialized = False
