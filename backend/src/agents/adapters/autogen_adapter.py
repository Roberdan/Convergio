"""
AutoGen Framework Adapter (I2)
Provides AutoGen fallback support for the unified adapter interface.
"""

from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

import structlog

from .framework_adapter import (
    FrameworkAdapter,
    FrameworkType,
    AgentMessage,
    AgentResponse,
)

# AutoGen imports with fallback
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    TextMessage = None

logger = structlog.get_logger()


class AutoGenAdapter(FrameworkAdapter):
    """AutoGen framework adapter.

    Provides backward compatibility with AutoGen-based agents.
    Uses AutoGen 0.7.x+ API with AssistantAgent.
    """

    def __init__(self, name: str = "autogen_adapter"):
        super().__init__(name)
        self.framework_type = FrameworkType.AUTOGEN
        self.model_client = None
        self.agent_loader = None

    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """Initialize AutoGen adapter.

        Args:
            agents_dir: Directory containing agent definitions
            model_client: AutoGen model client
            **kwargs: Additional configuration

        Returns:
            True if successful
        """
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen not available, cannot initialize adapter")
            return False

        try:
            logger.info("AutoGenAdapter initializing", agents_dir=agents_dir)

            self.model_client = model_client

            # Try to use DynamicAgentLoader if available
            try:
                from ..services.agent_loader import DynamicAgentLoader
                self.agent_loader = DynamicAgentLoader(agents_dir)
                self.agent_loader.scan_and_load_agents()

                # Create AutoGen agents
                if model_client:
                    self.agents = self.agent_loader.create_autogen_agents(
                        model_client=model_client,
                        tools=kwargs.get("tools", [])
                    )
                else:
                    # Store metadata only without creating agents
                    for key, meta in self.agent_loader.agent_metadata.items():
                        self.agents[key] = {"metadata": meta, "instance": None}

            except Exception as e:
                logger.warning(f"Agent loader not available: {e}")
                # Create minimal mock agents
                self.agents = {}

            self.is_initialized = True
            logger.info(
                "AutoGenAdapter initialized",
                agent_count=len(self.agents),
                autogen_version="0.7.x"
            )
            return True

        except Exception as e:
            logger.error(f"AutoGenAdapter initialization failed: {e}")
            return False

    async def execute(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """Execute AutoGen agent.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Returns:
            AgentResponse with result
        """
        if not AUTOGEN_AVAILABLE:
            return AgentResponse(
                content="AutoGen not available",
                agent_name=agent_key,
                success=False,
                error="AutoGen not installed",
                framework=self.framework_type
            )

        start = datetime.now()

        agent = self.agents.get(agent_key)
        if not agent:
            self._record_call(False, 0.0)
            return AgentResponse(
                content=f"Agent '{agent_key}' not found",
                agent_name=agent_key,
                success=False,
                error="Agent not found",
                framework=self.framework_type
            )

        try:
            # Create task message
            task_message = TextMessage(content=message, source="user")

            # Check if agent is an instance or metadata dict
            if isinstance(agent, dict) and agent.get("instance"):
                agent_instance = agent["instance"]
            elif hasattr(agent, "run"):
                agent_instance = agent
            else:
                # Need to create agent instance
                self._record_call(False, 0.0)
                return AgentResponse(
                    content="Agent not properly initialized",
                    agent_name=agent_key,
                    success=False,
                    error="Agent instance required",
                    framework=self.framework_type
                )

            # Execute agent
            result = await agent_instance.run(task=task_message)

            # Extract response
            messages = []
            final_response = ""

            if hasattr(result, 'messages'):
                for msg in result.messages:
                    messages.append(AgentMessage(
                        content=getattr(msg, 'content', str(msg)),
                        source=getattr(msg, 'source', 'unknown'),
                        role="assistant" if getattr(msg, 'source', '') != 'user' else "user"
                    ))
                    if getattr(msg, 'source', '') == agent_key:
                        final_response = getattr(msg, 'content', str(msg))

                # If no agent message found, get last non-user message
                if not final_response:
                    for msg in reversed(result.messages):
                        if getattr(msg, 'source', '') != 'user':
                            final_response = getattr(msg, 'content', str(msg))
                            break
            else:
                final_response = str(result)

            duration = (datetime.now() - start).total_seconds()
            self._record_call(True, duration)

            return AgentResponse(
                content=final_response,
                agent_name=agent_key,
                messages=messages,
                success=True,
                framework=self.framework_type,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self._record_call(False, duration)
            logger.error(f"AutoGen execution failed: {e}")
            return AgentResponse(
                content=f"Execution error: {str(e)}",
                agent_name=agent_key,
                success=False,
                error=str(e),
                framework=self.framework_type,
                duration_seconds=duration
            )

    async def execute_stream(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[AgentMessage, None]:
        """Stream AutoGen agent response.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Yields:
            AgentMessage chunks
        """
        if not AUTOGEN_AVAILABLE:
            yield AgentMessage(
                content="AutoGen not available",
                source="error",
                role="system"
            )
            return

        agent = self.agents.get(agent_key)
        if not agent:
            yield AgentMessage(
                content=f"Agent '{agent_key}' not found",
                source="error",
                role="system"
            )
            return

        try:
            # Get agent instance
            if isinstance(agent, dict) and agent.get("instance"):
                agent_instance = agent["instance"]
            elif hasattr(agent, "run_stream"):
                agent_instance = agent
            else:
                yield AgentMessage(
                    content="Agent not properly initialized for streaming",
                    source="error",
                    role="system"
                )
                return

            # Stream response
            async for chunk in agent_instance.run_stream(task=message):
                content = getattr(chunk, 'content', str(chunk))
                source = getattr(chunk, 'source', agent_key)

                yield AgentMessage(
                    content=content,
                    source=source,
                    role="assistant"
                )

        except Exception as e:
            logger.error(f"AutoGen streaming failed: {e}")
            yield AgentMessage(
                content=f"Streaming error: {str(e)}",
                source="error",
                role="system"
            )

    def get_agent(self, agent_key: str) -> Optional[Any]:
        """Get AutoGen agent instance."""
        agent = self.agents.get(agent_key)
        if isinstance(agent, dict):
            return agent.get("instance")
        return agent

    def list_agents(self) -> List[str]:
        """List available AutoGen agents."""
        return list(self.agents.keys())

    async def shutdown(self) -> None:
        """Shutdown AutoGen adapter."""
        logger.info("AutoGenAdapter shutting down")
        self.agents.clear()
        self.model_client = None
        self.agent_loader = None
        self.is_initialized = False


__all__ = ["AutoGenAdapter", "AUTOGEN_AVAILABLE"]
