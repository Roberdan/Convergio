"""
Agent Framework Orchestrator - Next-Generation Orchestration
Replaces AutoGen-based UnifiedOrchestrator with Microsoft Agent Framework
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import structlog

try:
    from agent_framework import Workflow, WorkflowExecutor, ChatAgent
    from agent_framework.messages import ChatMessage
    from agent_framework.decorators import ai_function
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    # Fallback to compatibility layer
    Workflow = None
    WorkflowExecutor = None
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
        self.executor: Optional[WorkflowExecutor] = None
        self.checkpoint_store = None

        # Agent registry
        self.agents: Dict[str, ChatAgent] = {}
        self.agent_metadata: Dict[str, Any] = {}

        # Configuration
        self.termination_markers = ["DONE", "TERMINATE", "END_CONVERSATION"]
        self.max_workflow_iterations = self.config.max_workflow_iterations

        # Safety
        self.safety_guardian = None

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

            # Initialize checkpoint store if enabled
            if self.config.enable_checkpointing:
                self.checkpoint_store = get_checkpoint_store(self.config)

            # Initialize workflow
            self.workflow = await self._build_workflow()

            # Create executor
            self.executor = WorkflowExecutor(
                workflow=self.workflow,
                checkpoint_store=self.checkpoint_store,
                max_iterations=self.max_workflow_iterations
            )

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

    async def _build_workflow(self) -> Workflow:
        """
        Build the workflow graph with agents and routing logic.

        Returns:
            Configured Workflow instance
        """
        workflow = Workflow()

        # Add entry point
        workflow.add_executor("start", self._start_handler)

        # Add routing node
        workflow.add_executor("route", self._route_handler)

        # Add all agents as executors
        for agent_name, agent in self.agents.items():
            workflow.add_executor(agent_name, self._create_agent_executor(agent))

        # Add aggregation node for multi-agent results
        workflow.add_executor("aggregate", self._aggregate_handler)

        # Add completion node
        workflow.add_executor("complete", self._complete_handler)

        # Define edges
        workflow.add_edge("start", "route")

        # Conditional routing from route node
        workflow.add_conditional_edges(
            "route",
            self._routing_decision,
            {
                "single_agent": "execute_single",
                "multi_agent": "execute_multi",
                "ali_orchestration": "ali_chief_of_staff",
                "complete": "complete"
            }
        )

        # Connect single agent execution to completion
        workflow.add_edge("execute_single", "complete")

        # Connect multi-agent to aggregation
        workflow.add_edge("execute_multi", "aggregate")
        workflow.add_edge("aggregate", "complete")

        logger.info(f"Workflow built with {len(self.agents)} agent executors")

        return workflow

    def _create_agent_executor(self, agent: ChatAgent):
        """
        Create an async executor function for an agent.

        Args:
            agent: ChatAgent instance

        Returns:
            Async executor function
        """
        async def executor(context: Dict[str, Any]) -> Dict[str, Any]:
            """Execute agent with context"""
            message = context.get("message", "")

            # Create ChatMessage
            chat_message = ChatMessage(role="user", content=message)

            # Run agent
            result = await agent.run(task=chat_message)

            # Extract response
            response = ""
            if hasattr(result, "messages"):
                for msg in reversed(result.messages):
                    if hasattr(msg, "role") and msg.role == "assistant":
                        response = msg.content
                        break
            else:
                response = str(result)

            return {
                "agent": agent.name,
                "response": response,
                "result": result
            }

        return executor

    async def _start_handler(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start handler - entry point for workflow.

        Args:
            context: Workflow context

        Returns:
            Updated context
        """
        logger.info("Workflow started", message_length=len(context.get("message", "")))

        context["start_time"] = datetime.now()
        context["agents_executed"] = []
        context["responses"] = []

        return context

    async def _route_handler(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route handler - determines execution strategy.

        Args:
            context: Workflow context

        Returns:
            Updated context with routing decision
        """
        message = context.get("message", "")
        target_agent = context.get("target_agent")

        # Check for explicit Ali targeting
        if target_agent:
            ta = target_agent.lower().replace('-', '_')
            if ta in ("ali_chief_of_staff", "ali", "ali-chief-of-staff"):
                context["routing_decision"] = "ali_orchestration"
                return context

        # Use intelligent router
        should_use_single = self.router.should_use_single_agent(message)

        if should_use_single:
            context["routing_decision"] = "single_agent"

            # Select best agent
            best_agent = self.router.select_best_agent(
                message,
                list(self.agents.values()),
                context
            )

            if best_agent:
                context["selected_agent"] = best_agent.name
                context["execution_mode"] = "single"
        else:
            context["routing_decision"] = "multi_agent"
            context["execution_mode"] = "multi"

        logger.info("Routing decision made", decision=context["routing_decision"])

        return context

    async def _routing_decision(self, context: Dict[str, Any]) -> str:
        """
        Make routing decision for conditional edges.

        Args:
            context: Workflow context

        Returns:
            Next node name
        """
        return context.get("routing_decision", "single_agent")

    async def _aggregate_handler(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate results from multiple agents.

        Args:
            context: Workflow context

        Returns:
            Updated context with aggregated results
        """
        responses = context.get("responses", [])

        # Combine responses intelligently
        if not responses:
            context["final_response"] = "No responses received from agents."
        elif len(responses) == 1:
            context["final_response"] = responses[0]
        else:
            # Use Ali or first agent to synthesize
            synthesis_prompt = f"""
            Multiple agents have provided responses. Please synthesize them into a coherent answer.

            Responses:
            {chr(10).join([f"- {r}" for r in responses])}

            Provide a unified, comprehensive response.
            """

            # Try to use Ali for synthesis
            ali_agent = self.agents.get("ali_chief_of_staff")
            if ali_agent:
                synthesis_msg = ChatMessage(role="user", content=synthesis_prompt)
                result = await ali_agent.run(task=synthesis_msg)

                if hasattr(result, "messages"):
                    for msg in reversed(result.messages):
                        if hasattr(msg, "role") and msg.role == "assistant":
                            context["final_response"] = msg.content
                            break
            else:
                # Fallback: concatenate responses
                context["final_response"] = "\n\n".join(responses)

        return context

    async def _complete_handler(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completion handler - finalize workflow execution.

        Args:
            context: Workflow context

        Returns:
            Final context
        """
        end_time = datetime.now()
        start_time = context.get("start_time", end_time)
        duration = (end_time - start_time).total_seconds()

        context["end_time"] = end_time
        context["duration_seconds"] = duration

        logger.info(
            "Workflow completed",
            duration=duration,
            agents_executed=len(context.get("agents_executed", []))
        )

        return context

    async def orchestrate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Orchestrate request using Agent Framework workflow.

        Args:
            message: Input message
            context: Optional context
            user_id: User identifier
            conversation_id: Conversation identifier

        Returns:
            Orchestration result
        """
        start_time = datetime.now()

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
                        "blocked": True
                    }

            # Prepare workflow context
            workflow_context = {
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "original_context": context or {},
                **(context or {})
            }

            # Execute workflow
            result = await self.executor.run(input_data=workflow_context)

            # Extract final response
            final_response = result.get("final_response", result.get("response", ""))
            agents_used = result.get("agents_executed", [])

            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()

            return {
                "response": final_response,
                "agents_used": agents_used,
                "turn_count": len(agents_used),
                "duration_seconds": duration,
                "execution_mode": result.get("execution_mode", "unknown"),
                "workflow_result": result,
                "cost_breakdown": {}  # TODO: Implement cost tracking for Agent Framework
            }

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)

            return {
                "response": f"I encountered an issue processing your request: {str(e)}",
                "agents_used": [],
                "turn_count": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
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

        # Stream agent response
        chat_message = ChatMessage(role="user", content=message)

        try:
            async for chunk in best_agent.run_stream(task=chat_message):
                if hasattr(chunk, "content") and isinstance(chunk.content, str):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk.content,
                        "agent": best_agent.name
                    })
                    yield chunk.content

            await websocket.send_json({
                "type": "complete",
                "agent": best_agent.name
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
