"""
Framework Adapter Interface (I1)
Provides unified interface for Agent Framework and AutoGen.
Enables seamless switching and fallback between frameworks.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import structlog

logger = structlog.get_logger()


class FrameworkType(Enum):
    """Supported agent frameworks."""
    AGENT_FRAMEWORK = "agent_framework"
    AUTOGEN = "autogen"
    MOCK = "mock"


@dataclass
class AgentMessage:
    """Unified message format across frameworks."""
    content: str
    source: str
    role: str = "assistant"  # 'user', 'assistant', 'system'
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentResponse:
    """Unified response format."""
    content: str
    agent_name: str
    messages: List[AgentMessage] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    framework: FrameworkType = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FrameworkAdapter(ABC):
    """Abstract adapter interface for agent frameworks.

    Provides a unified interface regardless of which framework
    is being used (Agent Framework, AutoGen, or Mock).
    """

    def __init__(self, name: str = "adapter"):
        """Initialize adapter.

        Args:
            name: Adapter identifier
        """
        self.name = name
        self.is_initialized = False
        self.framework_type: FrameworkType = FrameworkType.MOCK
        self.agents: Dict[str, Any] = {}
        self._stats = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_duration": 0.0
        }

    @abstractmethod
    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """Initialize the adapter with agents.

        Args:
            agents_dir: Directory containing agent definitions
            model_client: Optional model client
            **kwargs: Additional configuration

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    async def execute(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """Execute an agent with a message.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Returns:
            AgentResponse with result
        """
        pass

    @abstractmethod
    async def execute_stream(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[AgentMessage, None]:
        """Stream agent response.

        Args:
            agent_key: Agent identifier
            message: User message
            context: Optional context
            **kwargs: Additional parameters

        Yields:
            AgentMessage chunks
        """
        pass

    @abstractmethod
    def get_agent(self, agent_key: str) -> Optional[Any]:
        """Get agent instance by key.

        Args:
            agent_key: Agent identifier

        Returns:
            Agent instance or None
        """
        pass

    @abstractmethod
    def list_agents(self) -> List[str]:
        """List available agent keys.

        Returns:
            List of agent identifiers
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown adapter and cleanup resources."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics.

        Returns:
            Dict with stats
        """
        avg_duration = 0.0
        if self._stats["calls"] > 0:
            avg_duration = self._stats["total_duration"] / self._stats["calls"]

        return {
            "name": self.name,
            "framework": self.framework_type.value,
            "initialized": self.is_initialized,
            "agent_count": len(self.agents),
            "calls": self._stats["calls"],
            "successes": self._stats["successes"],
            "failures": self._stats["failures"],
            "success_rate": self._stats["successes"] / max(self._stats["calls"], 1),
            "avg_duration_seconds": avg_duration
        }

    def _record_call(self, success: bool, duration: float) -> None:
        """Record call statistics.

        Args:
            success: Whether call succeeded
            duration: Call duration in seconds
        """
        self._stats["calls"] += 1
        self._stats["total_duration"] += duration
        if success:
            self._stats["successes"] += 1
        else:
            self._stats["failures"] += 1


class MockFrameworkAdapter(FrameworkAdapter):
    """Mock adapter for testing and fallback.

    Provides simulated responses when no real framework is available.
    """

    def __init__(self, name: str = "mock_adapter"):
        super().__init__(name)
        self.framework_type = FrameworkType.MOCK

    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """Initialize mock adapter."""
        logger.info("MockFrameworkAdapter initializing", agents_dir=agents_dir)

        # Create mock agents
        self.agents = {
            "mock_agent_1": {"name": "Mock Agent 1", "role": "General"},
            "mock_agent_2": {"name": "Mock Agent 2", "role": "Assistant"},
        }

        self.is_initialized = True
        logger.info("MockFrameworkAdapter initialized", agent_count=len(self.agents))
        return True

    async def execute(
        self,
        agent_key: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResponse:
        """Execute mock agent."""
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

        # Generate mock response
        response_content = f"[Mock Response from {agent['name']}] Received: {message[:100]}"

        duration = (datetime.now() - start).total_seconds()
        self._record_call(True, duration)

        return AgentResponse(
            content=response_content,
            agent_name=agent_key,
            messages=[
                AgentMessage(content=message, source="user", role="user"),
                AgentMessage(content=response_content, source=agent_key, role="assistant")
            ],
            success=True,
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
        """Stream mock agent response."""
        import asyncio

        agent = self.agents.get(agent_key)
        if not agent:
            yield AgentMessage(
                content=f"Agent '{agent_key}' not found",
                source="error",
                role="system"
            )
            return

        response = f"[Mock Stream from {agent['name']}] Received: {message[:50]}"
        words = response.split()

        for word in words:
            yield AgentMessage(
                content=word + " ",
                source=agent_key,
                role="assistant"
            )
            await asyncio.sleep(0.05)

    def get_agent(self, agent_key: str) -> Optional[Any]:
        """Get mock agent."""
        return self.agents.get(agent_key)

    def list_agents(self) -> List[str]:
        """List mock agents."""
        return list(self.agents.keys())

    async def shutdown(self) -> None:
        """Shutdown mock adapter."""
        logger.info("MockFrameworkAdapter shutting down")
        self.agents.clear()
        self.is_initialized = False


# Factory function
def create_adapter(
    framework: FrameworkType = FrameworkType.MOCK,
    name: str = "adapter"
) -> FrameworkAdapter:
    """Create a framework adapter.

    Args:
        framework: Framework type to use
        name: Adapter name

    Returns:
        FrameworkAdapter instance
    """
    if framework == FrameworkType.MOCK:
        return MockFrameworkAdapter(name)
    elif framework == FrameworkType.AGENT_FRAMEWORK:
        # Import here to avoid circular imports
        try:
            from .agent_framework_adapter import AgentFrameworkAdapter
            return AgentFrameworkAdapter(name)
        except ImportError:
            logger.warning("Agent Framework adapter not available, using mock")
            return MockFrameworkAdapter(name)
    elif framework == FrameworkType.AUTOGEN:
        try:
            from .autogen_adapter import AutoGenAdapter
            return AutoGenAdapter(name)
        except ImportError:
            logger.warning("AutoGen adapter not available, using mock")
            return MockFrameworkAdapter(name)
    else:
        return MockFrameworkAdapter(name)


__all__ = [
    "FrameworkAdapter",
    "FrameworkType",
    "AgentMessage",
    "AgentResponse",
    "MockFrameworkAdapter",
    "create_adapter",
]
