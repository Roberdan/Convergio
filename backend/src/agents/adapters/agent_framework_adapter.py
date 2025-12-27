"""
Agent Framework Adapter
Provides Agent Framework support for the unified adapter interface.
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

# Agent Framework imports with fallback
try:
    from agent_framework import Agent
    from agent_framework.messages import TextMessage as AFTextMessage
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    Agent = None
    AFTextMessage = None

logger = structlog.get_logger()


class AgentFrameworkAdapter(FrameworkAdapter):
    """Microsoft Agent Framework adapter.

    Provides native Agent Framework support for the unified interface.
    """

    def __init__(self, name: str = "agent_framework_adapter"):
        super().__init__(name)
        self.framework_type = FrameworkType.AGENT_FRAMEWORK
        self.model_client = None
        self.agent_loader = None

    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """Initialize Agent Framework adapter.

        Args:
            agents_dir: Directory containing agent definitions
            model_client: Model client
            **kwargs: Additional configuration

        Returns:
            True if successful
        """
        if not AGENT_FRAMEWORK_AVAILABLE:
            logger.warning("Agent Framework not available, cannot initialize adapter")
            return False

        try:
            logger.info("AgentFrameworkAdapter initializing", agents_dir=agents_dir)

            self.model_client = model_client

            # Try to use AgentFrameworkLoader if available
            try:
                from ..services.agent_framework_loader import AgentFrameworkLoader
                self.agent_loader = AgentFrameworkLoader(agents_dir)

                # Load agents using AF loader
                self.agents = self.agent_loader.load_agents(
                    model_client=model_client,
                    tools=kwargs.get("tools", [])
                )

            except ImportError:
                # Fallback to basic agent loading
                logger.warning("AgentFrameworkLoader not available, using basic loading")
                self.agents = {}

            self.is_initialized = True
            logger.info(
                "AgentFrameworkAdapter initialized",
                agent_count=len(self.agents)
            )
            return True

        except Exception as e:
            logger.error(f"AgentFrameworkAdapter initialization failed: {e}")
            return False

    async def execute(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """Execute Agent Framework agent.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Returns:
            AgentResponse with result
        """
        if not AGENT_FRAMEWORK_AVAILABLE:
            return AgentResponse(
                content="Agent Framework not available",
                agent_name=agent_key,
                success=False,
                error="Agent Framework not installed",
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
            task = AFTextMessage(content=message, source="user") if AFTextMessage else message

            # Execute agent
            if hasattr(agent, "run"):
                result = await agent.run(task=task)
            else:
                # Fallback for non-standard agent interface
                self._record_call(False, 0.0)
                return AgentResponse(
                    content="Agent does not support run method",
                    agent_name=agent_key,
                    success=False,
                    error="Invalid agent interface",
                    framework=self.framework_type
                )

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
            elif hasattr(result, 'content'):
                final_response = result.content
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
            logger.error(f"Agent Framework execution failed: {e}")
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
        """Stream Agent Framework agent response.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Yields:
            AgentMessage chunks
        """
        if not AGENT_FRAMEWORK_AVAILABLE:
            yield AgentMessage(
                content="Agent Framework not available",
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
            # Create task message
            task = AFTextMessage(content=message, source="user") if AFTextMessage else message

            # Stream response
            if hasattr(agent, "run_stream"):
                async for chunk in agent.run_stream(task=task):
                    content = getattr(chunk, 'content', str(chunk))
                    source = getattr(chunk, 'source', agent_key)

                    yield AgentMessage(
                        content=content,
                        source=source,
                        role="assistant"
                    )
            else:
                # Fallback to non-streaming
                result = await self.execute(agent_key, message, context, **kwargs)
                yield AgentMessage(
                    content=result.content,
                    source=agent_key,
                    role="assistant"
                )

        except Exception as e:
            logger.error(f"Agent Framework streaming failed: {e}")
            yield AgentMessage(
                content=f"Streaming error: {str(e)}",
                source="error",
                role="system"
            )

    def get_agent(self, agent_key: str) -> Optional[Any]:
        """Get Agent Framework agent instance."""
        return self.agents.get(agent_key)

    def list_agents(self) -> List[str]:
        """List available Agent Framework agents."""
        return list(self.agents.keys())

    async def shutdown(self) -> None:
        """Shutdown Agent Framework adapter."""
        logger.info("AgentFrameworkAdapter shutting down")
        self.agents.clear()
        self.model_client = None
        self.agent_loader = None
        self.is_initialized = False


__all__ = ["AgentFrameworkAdapter", "AGENT_FRAMEWORK_AVAILABLE"]
