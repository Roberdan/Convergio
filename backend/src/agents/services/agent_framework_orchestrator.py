"""
Agent Framework Orchestrator
Orchestrates agent execution using Microsoft Agent Framework patterns.
Provides dual-framework support for gradual migration from AutoGen.
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from datetime import datetime
from dataclasses import dataclass
import structlog

# Agent Framework imports with fallback
try:
    from agent_framework import Agent, ChatCompletionClient, AgentThread
    from agent_framework.messages import TextMessage as AFTextMessage
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Agent = None
    ChatCompletionClient = None
    AgentThread = None
    AFTextMessage = None

# Optional autogen import for backward compatibility
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    TextMessage = None

from ..services.agent_framework_loader import (
    AgentFrameworkLoader,
    agent_framework_loader,
    AGENT_FRAMEWORK_AVAILABLE as LOADER_AF_AVAILABLE
)
from ..tools.tools_registry import get_tools_registry

logger = structlog.get_logger()


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    max_turns: int = 10
    timeout_seconds: float = 300.0
    enable_streaming: bool = True
    enable_tools: bool = True
    enable_memory: bool = True
    fallback_to_autogen: bool = True


@dataclass
class AgentExecutionResult:
    """Result of agent execution."""
    success: bool
    agent_key: str
    response: str
    messages: List[Dict[str, Any]]
    tokens_used: int = 0
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentFrameworkOrchestrator:
    """
    Orchestrates agent execution using Microsoft Agent Framework.

    Provides:
    - Single agent execution
    - Multi-agent workflow execution
    - Streaming response support
    - Thread/memory management
    - Graceful fallback to AutoGen if AF not available
    """

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        loader: Optional[AgentFrameworkLoader] = None
    ):
        """Initialize the orchestrator.

        Args:
            config: Orchestrator configuration
            loader: Agent loader instance (uses global if not provided)
        """
        self.config = config or OrchestratorConfig()
        self.loader = loader or agent_framework_loader
        self.registry = get_tools_registry()

        # Determine which framework to use
        self.framework = self._determine_framework()

        # Thread management for conversations
        self._threads: Dict[str, Any] = {}

        # Agent cache
        self._agent_cache: Dict[str, Any] = {}

        # Execution callbacks
        self._on_message_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []

        logger.info(
            "AgentFrameworkOrchestrator initialized",
            framework=self.framework,
            agent_framework_available=AGENT_FRAMEWORK_AVAILABLE,
            autogen_available=AUTOGEN_AVAILABLE,
            config=vars(self.config)
        )

    def _determine_framework(self) -> str:
        """Determine which framework to use."""
        if AGENT_FRAMEWORK_AVAILABLE:
            return "agent_framework"
        elif AUTOGEN_AVAILABLE and self.config.fallback_to_autogen:
            logger.warning("Agent Framework not available, falling back to AutoGen")
            return "autogen"
        else:
            logger.warning("No agent framework available, running in mock mode")
            return "mock"

    async def execute_single_agent(
        self,
        agent_key: str,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionResult:
        """
        Execute a single agent with a message.

        Args:
            agent_key: The agent identifier (e.g., 'ali_chief_of_staff')
            message: The user message
            conversation_id: Optional conversation ID for thread continuity
            context: Optional additional context

        Returns:
            AgentExecutionResult with the agent's response
        """
        start_time = datetime.now()

        try:
            logger.info(
                "Executing single agent",
                agent_key=agent_key,
                message_preview=message[:100],
                conversation_id=conversation_id
            )

            if self.framework == "agent_framework":
                result = await self._execute_with_agent_framework(
                    agent_key, message, conversation_id, context
                )
            elif self.framework == "autogen":
                result = await self._execute_with_autogen(
                    agent_key, message, conversation_id, context
                )
            else:
                result = self._execute_mock(agent_key, message)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time

            logger.info(
                "Agent execution completed",
                agent_key=agent_key,
                success=result.success,
                execution_time_ms=execution_time
            )

            return result

        except Exception as e:
            logger.error(
                "Agent execution failed",
                agent_key=agent_key,
                error=str(e)
            )
            return AgentExecutionResult(
                success=False,
                agent_key=agent_key,
                response="",
                messages=[],
                error=str(e)
            )

    async def _execute_with_agent_framework(
        self,
        agent_key: str,
        message: str,
        conversation_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> AgentExecutionResult:
        """Execute using Microsoft Agent Framework."""
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError("Agent Framework not installed")

        # Get or create agent
        agent = await self._get_or_create_agent_af(agent_key)
        if agent is None:
            return AgentExecutionResult(
                success=False,
                agent_key=agent_key,
                response="",
                messages=[],
                error=f"Agent not found: {agent_key}"
            )

        # Get or create thread for conversation
        thread = self._get_or_create_thread(conversation_id)

        # Create user message
        user_message = AFTextMessage(content=message, source="user")

        # Execute with agent
        messages = []
        response_text = ""

        async for msg in agent.run_stream(
            task=user_message,
            thread=thread
        ):
            messages.append({
                "role": msg.source if hasattr(msg, 'source') else "assistant",
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            })
            if hasattr(msg, 'content'):
                response_text = msg.content

        return AgentExecutionResult(
            success=True,
            agent_key=agent_key,
            response=response_text,
            messages=messages
        )

    async def _execute_with_autogen(
        self,
        agent_key: str,
        message: str,
        conversation_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> AgentExecutionResult:
        """Execute using AutoGen (fallback)."""
        if not AUTOGEN_AVAILABLE:
            raise ImportError("AutoGen not installed")

        # Get agent from loader
        agents = self.loader.agent_metadata
        if agent_key not in agents:
            return AgentExecutionResult(
                success=False,
                agent_key=agent_key,
                response="",
                messages=[],
                error=f"Agent not found: {agent_key}"
            )

        # For now, return a placeholder - full autogen integration
        # would require model_client setup
        metadata = agents[agent_key]
        return AgentExecutionResult(
            success=True,
            agent_key=agent_key,
            response=f"[AutoGen Mode] Agent {metadata.name} received: {message[:100]}",
            messages=[
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"Response from {metadata.name}"}
            ],
            metadata={"framework": "autogen", "agent_name": metadata.name}
        )

    def _execute_mock(
        self,
        agent_key: str,
        message: str
    ) -> AgentExecutionResult:
        """Execute in mock mode (no framework available)."""
        return AgentExecutionResult(
            success=True,
            agent_key=agent_key,
            response=f"[Mock Mode] Agent {agent_key} received message: {message[:100]}",
            messages=[
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"Mock response from {agent_key}"}
            ],
            metadata={"framework": "mock"}
        )

    async def _get_or_create_agent_af(self, agent_key: str) -> Optional[Any]:
        """Get or create an Agent Framework agent."""
        if agent_key in self._agent_cache:
            return self._agent_cache[agent_key]

        if not AGENT_FRAMEWORK_AVAILABLE:
            return None

        # Check if agent metadata exists
        if agent_key not in self.loader.agent_metadata:
            logger.warning(f"Agent metadata not found: {agent_key}")
            return None

        metadata = self.loader.agent_metadata[agent_key]

        # Create chat client and agent
        try:
            client = self.loader.get_chat_client("openai")
            tools = self.registry.get_all_tools() if self.config.enable_tools else []

            agent = Agent(
                name=metadata.key,
                model_client=client,
                system_message=self.loader._build_instructions(metadata),
                tools=tools
            )

            self._agent_cache[agent_key] = agent
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return None

    def _get_or_create_thread(self, conversation_id: Optional[str]) -> Any:
        """Get or create a conversation thread."""
        if conversation_id is None:
            conversation_id = f"thread_{datetime.now().timestamp()}"

        if conversation_id not in self._threads:
            if AGENT_FRAMEWORK_AVAILABLE and AgentThread:
                self._threads[conversation_id] = AgentThread()
            else:
                self._threads[conversation_id] = {"messages": []}

        return self._threads[conversation_id]

    async def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        initial_message: str,
        conversation_id: Optional[str] = None
    ) -> List[AgentExecutionResult]:
        """
        Execute a multi-agent workflow.

        Args:
            workflow: List of workflow steps, each with agent_key and optional config
            initial_message: Starting message for the workflow
            conversation_id: Optional conversation ID

        Returns:
            List of execution results for each step
        """
        results = []
        current_message = initial_message

        for i, step in enumerate(workflow):
            agent_key = step.get("agent_key")
            step_context = step.get("context", {})

            logger.info(f"Executing workflow step {i+1}/{len(workflow)}: {agent_key}")

            result = await self.execute_single_agent(
                agent_key=agent_key,
                message=current_message,
                conversation_id=conversation_id,
                context=step_context
            )

            results.append(result)

            if not result.success:
                logger.error(f"Workflow stopped at step {i+1} due to error")
                break

            # Use response as input for next step
            current_message = result.response

        return results

    async def stream_response(
        self,
        agent_key: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from an agent.

        Args:
            agent_key: The agent identifier
            message: The user message
            conversation_id: Optional conversation ID

        Yields:
            Response chunks as they become available
        """
        if not self.config.enable_streaming:
            result = await self.execute_single_agent(agent_key, message, conversation_id)
            yield result.response
            return

        if self.framework == "agent_framework" and AGENT_FRAMEWORK_AVAILABLE:
            agent = await self._get_or_create_agent_af(agent_key)
            if agent:
                thread = self._get_or_create_thread(conversation_id)
                user_message = AFTextMessage(content=message, source="user")

                async for msg in agent.run_stream(task=user_message, thread=thread):
                    if hasattr(msg, 'content'):
                        yield msg.content
            else:
                yield f"Agent {agent_key} not found"
        else:
            # Non-streaming fallback
            result = await self.execute_single_agent(agent_key, message, conversation_id)
            yield result.response

    def register_message_callback(self, callback: Callable) -> None:
        """Register a callback for message events."""
        self._on_message_callbacks.append(callback)

    def register_error_callback(self, callback: Callable) -> None:
        """Register a callback for error events."""
        self._on_error_callbacks.append(callback)

    def clear_thread(self, conversation_id: str) -> bool:
        """Clear a conversation thread."""
        if conversation_id in self._threads:
            del self._threads[conversation_id]
            return True
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        return {
            "framework": self.framework,
            "active_threads": len(self._threads),
            "cached_agents": len(self._agent_cache),
            "agent_framework_available": AGENT_FRAMEWORK_AVAILABLE,
            "autogen_available": AUTOGEN_AVAILABLE
        }


# Global orchestrator instance
_orchestrator_instance: Optional[AgentFrameworkOrchestrator] = None


def get_orchestrator(
    config: Optional[OrchestratorConfig] = None
) -> AgentFrameworkOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentFrameworkOrchestrator(config=config)
    return _orchestrator_instance


async def execute_agent(
    agent_key: str,
    message: str,
    conversation_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> AgentExecutionResult:
    """Convenience function to execute a single agent."""
    orchestrator = get_orchestrator()
    return await orchestrator.execute_single_agent(
        agent_key=agent_key,
        message=message,
        conversation_id=conversation_id,
        context=context
    )


__all__ = [
    "AgentFrameworkOrchestrator",
    "OrchestratorConfig",
    "AgentExecutionResult",
    "get_orchestrator",
    "execute_agent",
    "AGENT_FRAMEWORK_AVAILABLE",
    "AUTOGEN_AVAILABLE",
]
