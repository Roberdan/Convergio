"""
Agent Adapter - Provides compatibility between AutoGen and Agent Framework agents
"""

from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()


class AgentAdapter:
    """
    Adapter to provide compatibility between AutoGen AssistantAgent and
    Agent Framework ChatAgent during migration.
    """

    def __init__(self, agent: Any, framework: str = "autogen"):
        """
        Initialize adapter with an agent instance.

        Args:
            agent: Either AutoGen AssistantAgent or Agent Framework ChatAgent
            framework: "autogen" or "agent_framework"
        """
        self.agent = agent
        self.framework = framework
        self._validate_agent()

    def _validate_agent(self):
        """Validate that the agent has the required attributes"""
        required_attrs = ["name"]
        for attr in required_attrs:
            if not hasattr(self.agent, attr):
                logger.warning(
                    f"Agent missing required attribute: {attr}",
                    framework=self.framework,
                )

    @property
    def name(self) -> str:
        """Get agent name (works for both frameworks)"""
        return self.agent.name

    async def run(self, message: str, **kwargs) -> Any:
        """
        Run agent with message - adapts between frameworks.

        Args:
            message: Input message
            **kwargs: Additional arguments

        Returns:
            Response from agent
        """
        if self.framework == "autogen":
            # AutoGen uses TextMessage
            from autogen_agentchat.messages import TextMessage

            task = TextMessage(content=message, source="user")
            result = await self.agent.run(task=task)
            return result

        elif self.framework == "agent_framework":
            # Agent Framework uses ChatMessage
            try:
                from agent_framework.messages import ChatMessage

                task = ChatMessage(role="user", content=message)
                result = await self.agent.run(task=task)
                return result
            except ImportError:
                logger.error("Agent Framework not installed")
                raise

        else:
            raise ValueError(f"Unknown framework: {self.framework}")

    def get_tools(self) -> List[Any]:
        """Get agent's tools (compatible with both frameworks)"""
        if hasattr(self.agent, "tools"):
            return self.agent.tools or []
        return []

    def get_system_message(self) -> str:
        """Get agent's system message/instructions"""
        if self.framework == "autogen":
            return getattr(self.agent, "system_message", "")
        elif self.framework == "agent_framework":
            return getattr(self.agent, "instructions", "")
        return ""

    @classmethod
    def from_autogen(cls, autogen_agent: Any) -> "AgentAdapter":
        """Create adapter from AutoGen agent"""
        return cls(autogen_agent, framework="autogen")

    @classmethod
    def from_agent_framework(cls, af_agent: Any) -> "AgentAdapter":
        """Create adapter from Agent Framework agent"""
        return cls(af_agent, framework="agent_framework")

    def __repr__(self) -> str:
        return f"AgentAdapter(name={self.name}, framework={self.framework})"
